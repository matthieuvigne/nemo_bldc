import typing as tp
import numpy as np
from matplotlib.figure import Figure
import matplotlib as mpl
import matplotlib.cm as mcolormaps

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf

from .abstract_tab import AbstractTab
from .utils import *
from ..physics.battery import get_battery_state
from ..physics.motor import Motor

from ..ressources import get_ressource_path

DISPLAYED_CTES = [('Km, articular', 'Nm/\u221AW', lambda m: f"{m.K_m_art:.3f}"),
                  ('', 'W /Nm\u00B2', lambda m: f"{1 / m.K_m_art**2:.3f}"),
                  ('Power (non defluxing)', 'W', lambda m: f"{m.w_max_at_max_torque * m.iq_max * m.kt_q_art:.1f}"),
                  ('Ke', 'V/rad.s', lambda m: f"{m.ke:.3f}"),
                  ('Ktq, articular', 'Nm/A', lambda m: f"{m.kt_q_art:.3f}"),
                  ('Max torque, articular', 'Nm', lambda m: f"{m.tau_max:.1f}"),
                  ('No load speed, articular', 'rad/s', lambda m: f"{m.w_max_no_load:.1f}"),
                  ('', 'rpm', lambda m: f"{30 / np.pi * m.w_max_no_load:.0f}"),
                  ('Max speed @ max torque', 'rad/s', lambda m: f"{m.w_max_at_max_torque:.1f}"),
                  ('', 'rpm', lambda m: f"{30 / np.pi * m.w_max_at_max_torque:.0f}"),
                  ('R', 'Ohm', lambda m: f"{m.R:.3f}")]

class SingleMotorPerfTab(AbstractTab):
    '''
    GUI tab: look at the caracteristics of a single motor
    '''
    def __init__(self):
        builder = Gtk.Builder()
        builder.add_from_file(get_ressource_path("single_motor_tab.glade"))
        super().__init__("Single motor analysis", builder.get_object("side_box"))

        # Get the widgets we need from the builder.
        self.spin_bat_res = builder.get_object("spin_bat_res")
        self.spin_nominal_T = builder.get_object("spin_nominal_T")
        self.spin_flux_var = builder.get_object("spin_flux_var")
        self.spin_R_var = builder.get_object("spin_R_var")
        self.spin_rotor = builder.get_object("spin_rotor_temp")
        self.spin_stator = builder.get_object("spin_stator_temp")

        self.motors = [Motor(1, 0.01, 0.0001, 1.0, 1.0, 1.0, 1.0, 1.0) for _ in range(2)]

        self.label_specs = []
        for p in ["nominal_", "thermal_"]:
            self.label_specs.append(builder.get_object(f"{p}spec"))

        spec_legend = builder.get_object("spec_legend")
        spec_unit = builder.get_object("spec_unit")
        spec_legend.set_text("\n".join([d[0] for d in DISPLAYED_CTES]))
        spec_unit.set_text("\n".join([d[1] for d in DISPLAYED_CTES]))

        box = builder.get_object("side_box")
        box.pack_start(self.motor_widget.top_frame, False, False, 0)
        box.reorder_child(self.motor_widget.top_frame, 0)
        self.motor_widget.connect("motor_updated", self.input_updated)

        self.mpl_fig = Figure(figsize=(5, 4), dpi=100)
        ax = self.mpl_fig.add_subplot()
        self.mpl_fig.subplots_adjust(left=0.08, bottom=0.15, right=1.0, top=0.97, wspace=0, hspace=0)
        self.cbar = self.mpl_fig.colorbar(mpl.cm.ScalarMappable(mpl.colors.Normalize(vmin=0, vmax=1000)))

        self.configure_plot(self.mpl_fig)

        combo_box = builder.get_object("plot_type")
        self.change_plot_type(combo_box)
        builder.connect_signals(self)

    def input_updated(self, *args, **kargs):
        self.battery_resistance = self.spin_bat_res.get_value()

        self.motors[0] = self.motor_widget.motor
        To = self.spin_nominal_T.get_value()
        fvar = self.spin_flux_var.get_value() / 100.0
        Rvar = self.spin_R_var.get_value() / 100.0
        Tr = self.spin_rotor.get_value()
        Ts = self.spin_stator.get_value()
        self.motors[1].update_constants(
            n = 2 * self.motors[0].np,
            R = self.motors[0].R * (1 + Rvar * (Ts - To)),
            L = self.motors[0].L,
            ke = self.motors[0].ke * (1 - fvar * (Tr - To)),
            iq_max = self.motors[0].iq_max,
            iq_nominal = self.motors[0].iq_nominal,
            U = self.motors[0].U,
            reduction_ratio = self.motors[0].rho)

        for i in range(2):
            text = "\n".join([d[2](self.motors[i]) for d in DISPLAYED_CTES])
            self.label_specs[i].set_text(text)

        self.plot_need_update()

    def update_plot(self):
        # Use this for scaling & legend
        plot_caracteristics(self.mpl_fig.gca(), [self.motors[1]], ["C2"])
        # Next replot the curves in the right order
        plot_motor_caracteristic(self.mpl_fig.gca(), self.motors[0], "k")
        plot_motor_caracteristic(self.mpl_fig.gca(), self.motors[1], "C2")

        mot = self.motors[1]

        max_plot_speed = min(2 * mot.w_max_no_load, mot.compute_max_speed_deflux(0.0))
        w = np.linspace(0, max_plot_speed, 200)

        tau = np.linspace(0, mot.tau_max, 200)
        w_grid, tau_grid = np.meshgrid(w, tau)

        plot_surface = np.full(w_grid.shape, -np.inf)

        # Select plot content
        if self.plot_type[0] == "meca":
            plot_func = lambda t, w: t * w
        elif self.plot_type[0] == "thermal":
            plot_func = lambda t, w: mot.compute_thermal_power(t, w)
        elif self.plot_type[0] == "power":
            plot_func = lambda t, w: t * w + mot.compute_thermal_power(t, w)
        elif self.plot_type[0] == "efficiency":
            plot_func = lambda t, w: t * w / (t * w + mot.compute_thermal_power(t, w)) * 100
        elif self.plot_type[0] == "battery":
            plot_func = lambda t, w: get_battery_state(mot.U, self.battery_resistance,t * w + mot.compute_thermal_power(t, w))[0]

        for i in range(len(w_grid)):
            mask = w_grid[i] <= mot.compute_max_speed_deflux(tau_grid[i])
            plot_surface[i][mask] = plot_func(tau_grid[i][mask], w_grid[i][mask])
        ax = self.mpl_fig.gca()
        cm = mcolormaps.get_cmap("RdBu")
        cm = cm.reversed()
        cm.set_over('w')
        cm.set_under('#A0A0A0')
        ax.grid(False)
        q = ax.pcolormesh(w_grid, tau_grid, plot_surface, cmap=cm, shading='gouraud', rasterized=True)
        # Hide cursor data, the interpolation makes it wrong anyway.
        q.get_cursor_data = lambda event: None

        def format_coord(w, t):
            tail = ""
            if w < mot.compute_max_speed_deflux(t):
                tail = f", {self.plot_type[1]}: {plot_func(t, w):.1f}{self.plot_type[2]}"
            return f"Velocity: {w:.1f}rad/s ({w * 30 / np.pi:.1f}rpm), Torque: {t:.1f}Nm" + tail
        ax.format_coord = format_coord

        ax = self.cbar.ax
        ax.clear()
        self.cbar = self.mpl_fig.colorbar(mpl.cm.ScalarMappable(mpl.colors.Normalize(vmin=np.nanmin(plot_surface[plot_surface != -np.inf]), vmax=np.nanmax(plot_surface)), cmap=cm), cax = ax)
        ax.set_ylabel(self.plot_type[1])
        if self.plot_type[0] == "battery":
            sa = ax.secondary_yaxis(0.0,
                                    functions=(lambda u : (mot.U - u) / self.battery_resistance, lambda i : mot.U - self.battery_resistance * i))
            sa.set_ylabel('Battery current (A)', fontsize=10)

        self.mpl_fig.canvas.draw()

    def change_plot_type(self, combo_box):
        """
        Change the type of plot asked for
        """
        model = combo_box.get_model()
        self.plot_type = model[combo_box.get_active_iter()][1:]
        self.spin_bat_res.set_sensitive(self.plot_type[0] == "battery")
        self.plot_need_update()
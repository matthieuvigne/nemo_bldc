from logging.handlers import TimedRotatingFileHandler
import typing as tp
import numpy as np
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec
import math

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf

from .widget_motor_creation import DisplayMotor
from .abstract_tab import AbstractTab
from .widget_signal_config import SignalConfigWidget
from .widget_pi_config import PIConfigWidget
from .utils import *
from ..ressources import get_ressource_path

from ..simulation.pi_controller import PIController
from ..simulation.simulate import simulate, ControlType


def plot_position_tracking(ax, simulation_result):
    ax.plot(simulation_result.time, simulation_result.theta, label = "Mechanical angle")
    if simulation_result.control_type == ControlType.POSITION:
        ax.plot(simulation_result.time, simulation_result.pos_target, label = "Target angle")
    ax.set_ylabel("Position (rad)")
    ax.grid()
    ax.legend()

def plot_velocity_tracking(ax, simulation_result):
    ax.plot(simulation_result.time, simulation_result.dtheta, label = "Velocity")
    if simulation_result.control_type == ControlType.POSITION or simulation_result.control_type == ControlType.VELOCITY:
        ax.plot(simulation_result.time, simulation_result.vel_target, label = "Target velocity")
    ax.set_ylabel("Velocity (rad/s)")
    ax.grid()
    ax.legend()

def plot_idq(ax, simulation_result):
    ax.plot(simulation_result.time, simulation_result.idq[1], label = "Quadrature current")
    ax.plot(simulation_result.time, simulation_result.idq_target[1], label = "Quadrature current target")
    ax.plot(simulation_result.time, simulation_result.idq[0], label = "Direct current")
    ax.plot(simulation_result.time, simulation_result.idq_target[0], label = "Direct current target")
    ax.set_ylabel("Current (A)")
    ax.axhline(-simulation_result.motor.iq_max, color="k", linestyle="dashed")
    ax.axhline(simulation_result.motor.iq_max, color="k", linestyle="dashed")
    ax.set_ylim(-1.05 * simulation_result.motor.iq_max, 1.05 * simulation_result.motor.iq_max)
    ax.grid()
    ax.legend()

def plot_vdq(ax, simulation_result):
    ax.plot(simulation_result.time, simulation_result.Vdq_target[1], color="C2", label = "Quadrature voltage target")
    ax.plot(simulation_result.time, simulation_result.Vdq_target[0], color="C3", label = "Direct voltage target")
    ax.plot(simulation_result.time, simulation_result.Vdq[1], label = "Quadrature voltage")
    ax.plot(simulation_result.time, simulation_result.Vdq[0], label = "Direct voltage")
    ax.set_ylabel("Voltage (V)")
    um = simulation_result.motor.U / np.sqrt(3)
    ax.axhline(-um, color="k", linestyle="dashed")
    ax.axhline(um, color="k", linestyle="dashed")
    ax.set_ylim(-1.05 * um, 1.05 * um)
    ax.grid()
    ax.legend()

def plot_iphase(ax, simulation_result):
    ax.plot(simulation_result.time, simulation_result.iphase[0], label = "Current phase A")
    ax.plot(simulation_result.time, simulation_result.iphase[1], label = "Current phase B")
    ax.plot(simulation_result.time, simulation_result.iphase[2], label = "Current phase C")
    ax.set_ylabel("Current (A)")
    ax.axhline(-simulation_result.motor.iq_max, color="k", linestyle="dashed")
    ax.axhline(simulation_result.motor.iq_max, color="k", linestyle="dashed")
    ax.set_ylim(-1.05 * simulation_result.motor.iq_max, 1.05 * simulation_result.motor.iq_max)
    ax.grid()
    ax.legend()

def plot_uphase(ax, simulation_result):
    ax.plot(simulation_result.time, simulation_result.Vphase[0], label = "Voltage phase A")
    ax.plot(simulation_result.time, simulation_result.Vphase[1], label = "Voltage phase B")
    ax.plot(simulation_result.time, simulation_result.Vphase[2], label = "Voltage phase C")
    ax.set_ylabel("Voltage (V)")
    um = simulation_result.motor.U / np.sqrt(3)
    ax.axhline(-um, color="k", linestyle="dashed")
    ax.axhline(um, color="k", linestyle="dashed")
    ax.set_ylim(-1.05 * um, 1.05 * um)
    ax.grid()
    ax.legend()

SIMULATION_PLOTS = [("Position tracking", True, plot_position_tracking),
                    ("Velocity tracking", True, plot_velocity_tracking),
                    ("Current tracking", True, plot_idq),
                    ("Quadrature / direct voltage", True, plot_vdq),
                    ("Phase current", True, plot_iphase),
                    ("Phase voltage", True, plot_uphase),
                   ]

class SimulateMotor(AbstractTab):
    """
    GUI tab: compare two motors
    """

    def __init__(self):
        builder = Gtk.Builder()
        builder.add_from_file(get_ressource_path("simulation_tab.glade"))
        super().__init__("Simulation", builder.get_object("box_toplevel"))

        # Get the widgets we need from the builder.
        self.spin_duration = builder.get_object("spin_duration")
        self.spin_frequency = builder.get_object("spin_frequency")
        self.spin_inertia = builder.get_object("spin_inertia")
        self.spin_nu = builder.get_object("spin_nu")
        self.combo_box_type = builder.get_object("combo_box_type")

        self.input_signal_widget = SignalConfigWidget("Input signal")

        self.mpl_fig = Figure(figsize=(5, 4), dpi=100)

        self.configure_plot(self.mpl_fig, True)
        self.result = None

        box = builder.get_object("box_basic")
        box.pack_start(self.input_signal_widget.frame, False, False, 0)
        box.pack_start(self.motor_widget.top_frame, False, False, 0)
        box.reorder_child(builder.get_object("frame_plot_option"), 3)

        # Populate plot grid
        grid = builder.get_object("grid_plot_options")
        self.plot_buttons = []
        for i, (label, active, _) in enumerate(SIMULATION_PLOTS):
            b = Gtk.CheckButton(label=label)
            b.set_active(active)
            b.connect("toggled", self.plot_config_update)

            self.plot_buttons.append(b)
            grid.attach(b, i % 2, i // 2, 1, 1)


        box = builder.get_object("box_advanced")
        self.direct_current_signal_widget = SignalConfigWidget("Direct current target value")
        box.pack_start(self.direct_current_signal_widget.frame, False, False, 0)
        self.load_signal_widget = SignalConfigWidget("Additional load torque")
        box.pack_start(self.load_signal_widget.frame, False, False, 0)
        self.current_pi_widget = PIConfigWidget("Current loop PI gains", "V/A")
        box.pack_start(self.current_pi_widget.frame, False, False, 0)
        self.velocity_pi_widget = PIConfigWidget("Velocity loop PI gains", "A/(rad/s)")
        box.pack_start(self.velocity_pi_widget.frame, False, False, 0)
        self.position_pi_widget = PIConfigWidget("Position loop PI gains", "(rad/s)/rad", "rad/s")
        box.pack_start(self.position_pi_widget.frame, False, False, 0)

        # "Reasonable" initial guess for typical applications
        self.current_pi_widget.set_gains(1.0, 100.0, 10.0)
        self.velocity_pi_widget.set_gains(5.0, 5.0, 10.0)
        self.position_pi_widget.set_gains(10.0, 0.5, 10.0)

        builder.connect_signals(self)

    def run_clicked(self, button):
        tree_iter = self.combo_box_type.get_active_iter()
        if tree_iter is None:
            return
        control_type = self.combo_box_type.get_model()[tree_iter][1]

        try:
            self.result = simulate(self.motor_widget.motor,
                               ControlType[control_type],
                               self.input_signal_widget.signal,
                               self.spin_duration.get_value(),
                               self.spin_inertia.get_value(),
                               self.spin_nu.get_value(),
                               self.current_pi_widget.controller,
                               self.velocity_pi_widget.controller,
                               self.position_pi_widget.controller,
                               self.spin_frequency.get_value(),
                               0.0,
                               self.direct_current_signal_widget.signal,
                               self.load_signal_widget.signal,
                               )
        except ArithmeticError as e:
            dialog = Gtk.MessageDialog(
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="Warning: an error occured during simulation !",
            )
            dialog.format_secondary_text(str(e))
            dialog.run()
            dialog.destroy()

        self.user_asked_for_update()

    def plot_config_update(self, button):
        if self.result is not None:
            self.plot_need_update()

    def update_plot(self):
        if self.result is not None:
            self.mpl_fig.clear()
            n_plots = sum([1 if b.get_active() else 0 for b in self.plot_buttons])

            y = 3 if n_plots > 3 else n_plots
            x = math.ceil(n_plots / 3)
            gs = GridSpec(x, y, left = 0.05, right = 0.95, bottom = 0.05, top = 0.95, wspace = 0.2, hspace = 0.2)
            axs  = [self.mpl_fig.add_subplot(gs[i]) for i in range(n_plots)]
            callbacks = [callback for b, (_, _, callback) in zip(self.plot_buttons, SIMULATION_PLOTS) if b.get_active()]
            for a, callback in zip(axs, callbacks):
                a.sharex(axs[0])
                callback(a, self.result)
            n = min(n_plots, 3)
            for a in axs[-n:]:
                a.set_xlabel("Time (s)")
        self.mpl_fig.canvas.draw()

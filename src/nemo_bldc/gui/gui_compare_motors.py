import typing as tp
import numpy as np
from matplotlib.figure import Figure

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf

from .widget_motor_creation import DisplayMotor
from .abstract_tab import AbstractTab
from .utils import *
from ..ressources import get_ressource_path


def motor_to_treeview(mot):
    return [color_to_pixbuf(mot.get_gtk_color()),
            mot.name,
            f"{1 / mot.K_m_art**2:.4f}",
            f"{mot.kt_q_art:.3f}",
            f"{mot.nominal_power:.1f}"]

class CompareMotors(AbstractTab):
    '''
    GUI tab: compare two motors
    '''
    def __init__(self):
        builder = Gtk.Builder()
        builder.add_from_file(get_ressource_path("compare_tab.glade"))
        super().__init__("Compare", builder.get_object("side_box"))

        # Get the widgets we need from the builder.
        self.compare_entry_R = builder.get_object("compare_R")
        self.compare_entry_L = builder.get_object("compare_L")
        self.compare_entry_ke = builder.get_object("compare_ke")
        self.compare_entry_I = builder.get_object("compare_I")
        self.compare_entry_n = builder.get_object("compare_n")

        self.mpl_fig = Figure(figsize=(5, 4), dpi=100)
        ax = self.mpl_fig.add_subplot()
        self.mpl_fig.subplots_adjust(left=0.2, bottom=0.15, right=0.97, top=0.97, wspace=0, hspace=0)
        def format_coord(x, y):
            return f"Velocity: {x:.1f}rad/s ({x * 30 / np.pi:.1f}rpm), Torque: {y:.1f}Nm"
        ax.format_coord = format_coord

        self.configure_plot(self.mpl_fig)

        self.tree_view = builder.get_object("tree_view")
        self.tree_view.get_selection().connect("changed", self.tree_changed)
        self.motor_compare_list = builder.get_object("motor_compare_list")

        self.selected_motor = None
        self.motors = []

        box = builder.get_object("side_box")
        box.pack_start(self.motor_widget.top_frame, False, False, 0)
        box.reorder_child(self.motor_widget.top_frame, 2)
        self.motor_widget.connect("motor_updated", self.motor_updated)
        self.motor_widget.connect("motor_name_updated", self.motor_name_updated)

        self.motorList = builder.get_object("motorList")
        self.n_motor_created = 0

        self.grid_ctes = builder.get_object("grid_ctes")
        self.grid_column = []
        self.grid_sep = [Gtk.Separator() for _ in DISPLAYED_CTES]

        grid_labels = builder.get_object("grid_labels")
        for i, (field, unit, _) in enumerate(DISPLAYED_CTES):
            grid_labels.insert_row(2 * i + 1)
            grid_labels.attach(Gtk.Label(label=field), 0, 2 * i + 1, 1 ,1)
            grid_labels.attach(Gtk.Label(label=unit), 1, 2 * i + 1, 1, 1)
            grid_labels.insert_row(2 * i + 2)
            grid_labels.attach(Gtk.Separator(), 0, 2 * i + 2, 2, 1)

        builder.connect_signals(self)

    def param_update(self):
        for i, m in enumerate(self.motors):
            self.grid_column[i][0].set_markup(f"<b>{m.name}</b>")
            for (_, _, func), label in zip(DISPLAYED_CTES, self.grid_column[i][1:]):
                label.set_text(func(m))
        self.plot_need_update()

    def update_plot(self):
        plot_caracteristics(self.mpl_fig.gca(), self.motors, [m.color for m in self.motors])
        self.mpl_fig.canvas.draw()

    def motor_updated(self, *args):
        if self.selected_motor is not None:
            self.motors[self.selected_motor] = self.motor_widget.motor
            self.motor_compare_list[self.selected_motor][2] = f"{1 / self.motor_widget.motor.K_m_art**2:.3f}"
            self.motor_compare_list[self.selected_motor][3] = f"{self.motor_widget.motor.kt_q_art:.3f}"
            self.motor_compare_list[self.selected_motor][4] = f"{self.motor_widget.motor.nominal_power:.1f}"
            self.param_update(),

    def tree_changed(self, selection):
        # Get selection id
        model, treeiter = selection.get_selected()
        if treeiter is None:
            self.selected_motor = None
        else:
            self.selected_motor = int(str(model[treeiter].path))
            self.motor_widget.set_motor(self.motors[self.selected_motor])

    def add_motor(self, *args):
        name = list(self.motor_widget.motor_library.keys())[0]
        m = self.motor_widget.motor_library[name]
        mot = DisplayMotor(m, name,f"C{self.n_motor_created}")
        self.n_motor_created += 1
        self.motors.append(mot)
        self.motor_compare_list.append(motor_to_treeview(mot))

        # Create new column.
        nc = len(self.grid_column)
        self.grid_ctes.insert_column(2 * nc)
        self.grid_ctes.attach(Gtk.Separator(), 2 * nc, 0, 1, 2 * len(DISPLAYED_CTES) + 1)
        self.grid_ctes.insert_column(2 * nc + 1)
        self.grid_column.append([Gtk.Label(label='label')] + [Gtk.Label(label='label') for _ in DISPLAYED_CTES])
        for i, label in enumerate(self.grid_column[-1]):
            self.grid_ctes.attach(label, 2 * nc + 1, 2 * i - 1, 1, 1)
            self.grid_ctes.attach(Gtk.Separator(), 2 * nc + 1, 2 * i, 1, 1)

        self.grid_ctes.show_all()

        # Set cursor to new value
        self.tree_view.set_cursor(len(self.motors) - 1)

    def remove_motor(self, *args):
        if self.selected_motor is not None:
            idx = self.selected_motor
            del self.motors[idx]
            del self.grid_column[idx]
            self.motor_compare_list.clear()
            for mot in self.motors:
                self.motor_compare_list.append(motor_to_treeview(mot))
            self.tree_view.set_cursor(Gtk.TreePath())
            self.grid_ctes.remove_column(2 * idx)
            self.grid_ctes.remove_column(2 * idx)

    def motor_name_updated(self, *args):
        if self.selected_motor is not None:
            new_name = self.motor_widget.motor.name
            self.motors[self.selected_motor].name = new_name
            self.motor_compare_list[self.selected_motor][1] = new_name
            self.grid_column[self.selected_motor][0].set_text(new_name)

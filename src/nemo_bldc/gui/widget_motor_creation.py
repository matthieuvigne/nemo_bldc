import typing as tp
import numpy as np
import copy

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Gdk

import matplotlib.colors as mcolors
from ..physics.motor import Motor

from ..ressources import get_ressource_path

from .motor_creation_helper import MotorCreationHelper

class DisplayMotor(Motor):
    @staticmethod
    def FromJson(data):
        motor = Motor.FromDict(data)
        return DisplayMotor(motor, data["name"], data["color"])

    def __init__(self, motor, name, color):
        super().__init__(1, 1, 1, 1, 1, 1, 48, 1)
        super().copy(motor)

        self.name = name
        self.color = color

    def get_gtk_color(self):
        return Gdk.RGBA(*mcolors.to_rgba(self.color))

    def to_json(self):
        d = self.to_dict()
        d["name"] = self.name
        d["color"] = self.color
        return d

class MotorCreationWidget(GObject.Object):
    '''
    A widget for defining a motor from input parameters
    '''
    @GObject.Signal
    def motor_updated(self):
        pass

    @GObject.Signal
    def motor_name_updated(self):
        pass

    def __init__(self):
        GObject.GObject.__init__(self)
        builder = Gtk.Builder()
        builder.add_from_file(get_ressource_path("motor_creation_widget.glade"))
        self.top_frame = builder.get_object("top_frame")

        self.label_header = builder.get_object("header")

        self.entry_name = builder.get_object("entry_name")
        self.spin_R = builder.get_object("spin_R")
        self.spin_L = builder.get_object("spin_L")
        self.spin_ke = builder.get_object("spin_ke")
        self.spin_I = builder.get_object("spin_I")
        self.spin_np = builder.get_object("spin_np")
        self.spin_U = builder.get_object("spin_U")
        self.spin_rho = builder.get_object("spin_rho")
        self.spin_iqnom = builder.get_object("spin_iqnom")

        self.motor_box = builder.get_object("motor_box")
        self.motor_list = builder.get_object("motor_list")
        self.set_motor(DisplayMotor(Motor(1, 0.01, 0.0001, 1.0, 1.0, 1.0, 1.0, 1.0),
                                  "Name",
                                  "C0"))

        self.parent_callback = None
        builder.connect_signals(self)

    def set_motor(self, motor: DisplayMotor):
        self.motor = copy.copy(motor)
        self.entry_name.set_text(motor.name)
        self.spin_R.set_value(motor.R)
        self.spin_L.set_value(1000. * motor.L)
        self.spin_ke.set_value(motor.ke)
        self.spin_I.set_value(motor.iq_max)
        self.spin_iqnom.set_value(motor.iq_nominal)
        self.spin_iqnom.set_value(motor.iq_nominal)
        self.spin_np.set_value(2 * motor.np)
        self.spin_U.set_value(motor.U)
        self.spin_rho.set_value(motor.rho)
        self.motor_box.set_active(-1)
        self.input_updated()

    def input_updated(self, *args, **kargs):
        self.motor.update_constants(
            n = int(self.spin_np.get_value()),
            R = self.spin_R.get_value(),
            L = self.spin_L.get_value() / 1000.0,
            ke = self.spin_ke.get_value(),
            iq_max = self.spin_I.get_value(),
            iq_nominal = self.spin_iqnom.get_value(),
            U = self.spin_U.get_value(),
            reduction_ratio = self.spin_rho.get_value())
        self.emit("motor_updated")

    def name_updated(self, *args):
        self.motor.name = self.entry_name.get_text()
        self.emit("motor_name_updated")

    def box_updated(self, combo: tp.Any):
        tree_iter = combo.get_active_iter()
        if tree_iter is None:
            return
        name = combo.get_model()[tree_iter][0]

        self.motor.copy(self.motor_library[name])
        self.motor.name = name

        self.set_motor(self.motor)
        self.input_updated()

    def update_library(self, library):
        '''
        Update motor library.
        '''
        self.motor_library = library
        self.motor_list.clear()
        for n in self.motor_library:
            self.motor_list.append([n])
        self.motor_box.set_active(0)

    def ask_for_helper(self, button):
        helper = MotorCreationHelper(self.motor)
        result = helper.run()
        if result is not None:
            self.set_motor(DisplayMotor(result, self.motor.name, self.motor.color))


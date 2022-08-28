import typing as tp
import numpy as np
import copy

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject

from ..physics.motor import Motor
from ..ressources import get_ressource_path
from .utils import DISPLAYED_CTES

class MotorCreationHelper(GObject.Object):
    '''
    A widget for defining a motor from input parameters
    '''
    @GObject.Signal
    def motor_updated(self):
        pass

    @GObject.Signal
    def motor_name_updated(self):
        pass

    def __init__(self, motor):
        GObject.GObject.__init__(self)
        builder = Gtk.Builder()
        builder.add_from_file(get_ressource_path("motor_creation_helper.glade"))
        self.dialog = builder.get_object("dialog")
        self.dialog.set_title("Nemo - Motor creation helper")

        self.motor = Motor(1, 0.01, 0.0001, 1.0, 1.0, 1.0, 1.0, 1.0)

        self.toggle_winding = builder.get_object("toggle_winding")
        self.toggle_RL = builder.get_object("toggle_RL")
        self.toggle_current = builder.get_object("toggle_current")
        self.toggle_poles = builder.get_object("toggle_poles")

        self.box_mag = builder.get_object("box_mag")
        self.toggle_ke = builder.get_object("toggle_ke")
        self.toggle_kv = builder.get_object("toggle_kv")
        self.box_ke = builder.get_object("box_ke")
        self.box_kv = builder.get_object("box_kv")
        self.box_kt = builder.get_object("box_kt")

        self.toggle_ke_sp = builder.get_object("toggle_ke_sp")
        self.toggle_ke_pp = builder.get_object("toggle_ke_pp")
        self.toggle_ke_sp_rpm = builder.get_object("toggle_ke_sp_rpm")
        self.toggle_ke_pp_rpm = builder.get_object("toggle_ke_pp_rpm")
        self.toggle_kt_A = builder.get_object("toggle_kt_A")

        self.grid_labels = builder.get_object("grid_labels")
        self.ctes_labels = []
        for i, (field, unit, _) in enumerate(DISPLAYED_CTES):
            self.grid_labels.insert_row(2 * i + 1)
            self.grid_labels.attach(Gtk.Label(label=field), 0, 2 * i + 1, 1 ,1)
            self.grid_labels.attach(Gtk.Label(label=unit), 1, 2 * i + 1, 1, 1)
            self.grid_labels.insert_row(2 * i + 2)
            self.grid_labels.attach(Gtk.Separator(), 0, 2 * i + 2, 3, 1)
            l = Gtk.Label("")
            self.grid_labels.attach(l, 2, 2 * i + 1, 1, 1)
            self.ctes_labels.append(l)

        self.spin_R = builder.get_object("spin_R")
        self.spin_L = builder.get_object("spin_L")
        self.spin_ke = builder.get_object("spin_ke")
        self.spin_Inom = builder.get_object("spin_Inom")
        self.spin_Imax = builder.get_object("spin_Imax")
        self.spin_np = builder.get_object("spin_np")
        self.spin_U = builder.get_object("spin_U")

        self.spin_R.set_value(motor.R)
        self.spin_L.set_value(1000. * motor.L)
        self.spin_ke.set_value(motor.ke)
        self.spin_Inom.set_value(motor.iq_nominal)
        self.spin_Imax.set_value(motor.iq_max)
        self.spin_np.set_value(motor.np)
        self.spin_U.set_value(motor.U)

        self.label_R = builder.get_object("label_R")
        self.label_L = builder.get_object("label_L")
        self.label_ke = builder.get_object("label_ke")
        self.label_np = builder.get_object("label_np")
        self.label_inom = builder.get_object("label_inom")
        self.label_imax = builder.get_object("label_imax")

        builder.connect_signals(self)
        self.input_updated()

    def input_updated(self, *args, **kargs):
        '''
        Miscellaneous user input change: update motor and refresh display.
        '''
        is_delta = not self.toggle_winding.get_active()

        R = self.spin_R.get_value()
        L = self.spin_L.get_value() / 1000.0

        # Convert to single phase, star
        is_phase_to_phase = not self.toggle_RL.get_active()
        coeff = 0.5 if is_phase_to_phase else (1/3 if is_delta else 1)
        R *= coeff
        L *= coeff

        # Magnetic parameter
        val = self.spin_ke.get_value()
        if self.toggle_ke.get_active():
            if self.toggle_ke_sp.get_active():
                ke = val * 1/np.sqrt(3) if is_delta else 1
            elif self.toggle_ke_pp.get_active():
                ke = val / np.sqrt(3)
            elif self.toggle_ke_sp_rpm.get_active():
                ke = val * 30 / np.pi * 1/np.sqrt(3) if is_delta else 1
            else:
                ke = val * 30 / np.pi / np.sqrt(3)
        elif self.toggle_kv.get_active():
            ke = 1 / val * 30 / np.pi / np.sqrt(3)
        else:
            ktq = val * (1 if self.toggle_kt_A.get_active() else 1 / np.sqrt(2))
            ke = 2.0 / 3.0 * ktq

        npoles = int(self.spin_np.get_value())
        if not self.toggle_poles.get_active():
            npoles *= 2

        current_coeff = 1 if self.toggle_current.get_active() else np.sqrt(2)

        self.motor.update_constants(
            n = npoles,
            R = R,
            L = L,
            ke = ke,
            iq_max = current_coeff * self.spin_Imax.get_value(),
            iq_nominal = current_coeff * self.spin_Inom.get_value(),
            U = self.spin_U.get_value())

        # Update GUI
        self.label_R.set_text(f"{self.motor.R:.4f}")
        self.label_L.set_text(f"{1000 * self.motor.L:.4f}")
        self.label_ke.set_text(f"{self.motor.ke:.4f}")
        self.label_np.set_text(f"{int(2 * self.motor.np)}")
        self.label_inom.set_text(f"{self.motor.iq_nominal:.2f}")
        self.label_imax.set_text(f"{self.motor.iq_max:.2f}")

        for i, (_, _, f) in zip(self.ctes_labels, DISPLAYED_CTES):
            i.set_text(f(self.motor))

    def mag_updated(self, *args):
        '''
        User updated the magnetic parameter choice (Ke, Kv, Kt)
        '''
        if self.toggle_ke.get_active():
            act = self.box_ke
        elif self.toggle_kv.get_active():
            act = self.box_kv
        else:
            act = self.box_kt
        self.box_mag.remove(self.box_mag.get_children()[-1])
        self.box_mag.pack_end(act, True, True, 0)
        self.input_updated()

    def run(self):
        """
        Run the motor creation helper ; return the new motor, or None
        if the user canceled.
        """
        self.dialog.show_all()
        result = self.dialog.run()
        self.dialog.hide()
        if result == int(Gtk.ResponseType.OK):
            return self.motor
        return None
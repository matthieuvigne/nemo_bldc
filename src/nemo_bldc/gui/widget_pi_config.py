import typing as tp
import numpy as np

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from ..simulation.pi_controller import PIController

from ..ressources import get_ressource_path


class PIConfigWidget:
    """
    A class for configuring a PI controller
    """
    def __init__(self, name:str, kp_unit:str, ki_unit:tp.Optional[str] = None):
        builder = Gtk.Builder()
        builder.add_from_file(get_ressource_path("pi_config_widget.glade"))
        self.frame = builder.get_object("frame")

        builder.get_object("label_title").set_label(name)
        builder.get_object("label_kp").set_label(f"Kp ({kp_unit})")
        if ki_unit is None:
            ki_unit = kp_unit.split('/')[0]
        builder.get_object("label_max").set_label(f"Maximum integral correction ({ki_unit})")

        self.spin_kp = builder.get_object("spin_kp")
        self.spin_ki = builder.get_object("spin_ki")
        self.spin_max = builder.get_object("spin_max")

        builder.connect_signals(self)
        self.input_updated()

    def input_updated(self, *args, **kargs):
        self.controller = PIController(self.spin_kp.get_value(),
                                       self.spin_ki.get_value(),
                                       self.spin_max.get_value(),
                                    )

    def set_gains(self, Kp: float, Ki: float, integral_max: float):
        '''
        Set associated PI gains.
        '''
        self.spin_kp.set_value(Kp)
        self.spin_ki.set_value(Ki)
        self.spin_max.set_value(integral_max)
import typing as tp
import numpy as np
import copy

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from ..simulation.signal import create_signal

from ..ressources import get_ressource_path

class SignalConfigWidget:
    """
    A class for configuring an input signal for simulation
    """
    def __init__(self, name:str):
        builder = Gtk.Builder()
        builder.add_from_file(get_ressource_path("signal_config_widget.glade"))
        self.frame = builder.get_object("frame")

        builder.get_object("label_title").set_label(name)

        self.spin_freq = builder.get_object("spin_frequency")
        self.spin_phase = builder.get_object("spin_phase")
        self.spin_amplitude = builder.get_object("spin_amplitude")
        self.spin_offset = builder.get_object("spin_offset")
        self.combo_box_shape = builder.get_object("combo_box_shape")

        builder.connect_signals(self)
        self.input_updated()

    def input_updated(self, *args, **kargs):
        tree_iter = self.combo_box_shape.get_active_iter()
        if tree_iter is None:
            return
        signal_shape = self.combo_box_shape.get_model()[tree_iter][1]

        self.signal = create_signal(signal_shape,
                                    self.spin_freq.get_value(),
                                    self.spin_phase.get_value(),
                                    self.spin_amplitude.get_value(),
                                    self.spin_offset.get_value(),
                                    )

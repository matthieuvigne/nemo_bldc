import typing as tp
import numpy as np

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf

from matplotlib.backends.backend_gtk3agg import (
    FigureCanvasGTK3Agg as FigureCanvas)

from matplotlib.backends.backend_gtk3 import (
    NavigationToolbar2GTK3 as NavigationToolbar)

from matplotlib.figure import Figure

from .widget_motor_creation import MotorCreationWidget
from ..ressources import get_ressource_path

class AbstractTab:
    '''
    A tab of the analysis tool
    '''
    def __init__(self, name, sidebar_widget):
        sidebar_widget.set_size_request(300, -1)
        self.name = name

        builder = Gtk.Builder()
        builder.add_from_file(get_ressource_path("abstract_tab.glade"))
        self.tab_widget = builder.get_object("paned")
        # When designing in glade, the scroll widget is always the first
        # child: move it in second position.
        child = self.tab_widget.get_child1()
        self.tab_widget.remove(child)
        self.tab_widget.pack1(sidebar_widget, False, False)
        self.tab_widget.pack2(child, True, False)
        self.scroll_widget = builder.get_object("scroll_plot")
        self.motor_widget = MotorCreationWidget()
        builder.connect_signals(self)


    def configure_plot(self, matplotlib_plot):
        canvas = FigureCanvas(matplotlib_plot)
        canvas.set_size_request(800, 600)

        vbox = Gtk.VBox()
        toolbar = NavigationToolbar(canvas, self.scroll_widget)
        vbox.pack_start(toolbar, False, False, 0)
        vbox.pack_start(canvas, True, True, 0)

        self.button = Gtk.Button(label="Update plot")
        label = self.button.get_child()
        label.set_markup("<span size='x-large' foreground='red'><b>Update plot</b></span>")
        self.button.connect("clicked", self.user_asked_for_update)
        self.button.set_halign(Gtk.Align.CENTER)
        self.button.set_valign(Gtk.Align.START)
        self.button.set_margin_top(50)

        overlay = Gtk.Overlay()
        self.scroll_widget.add(overlay)
        overlay.add(vbox)
        overlay.add_overlay(self.button)

        self.button.set_visible(False)

    def plot_need_update(self):
        self.button.set_visible(True)

    def user_asked_for_update(self, *args):
        self.button.set_visible(False)
        self.update_plot()

    def update_library(self, library_data : "dict"):
        ''' Called when the main window library parameter has been updated '''
        self.motor_widget.update_library(library_data)

    def update_plot(self):
        pass

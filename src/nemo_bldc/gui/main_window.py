import typing as tp
from pathlib import Path
import numpy as np
import subprocess
import sys
import os

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

from ..ressources import get_ressource_path, load_motor_library
from ..doc import get_doc_path

class MainWindow:
    '''
    GUI tab: compare two motors
    '''
    def __init__(self):
        builder = Gtk.Builder()
        builder.add_from_file(get_ressource_path("main_window.glade"))
        self.window = builder.get_object("window")
        self.window = builder.get_object("window")
        # self.window.
        self.notebook = builder.get_object("notebook")
        self.tabs = []
        self.switch_external_window = builder.get_object("switch_external_window")
        self.external_window = Gtk.Window()
        self.external_window.set_title("Nemo - External viewer")
        self.external_window.set_deletable(False)
        self.external_window.set_size_request(600, 800)
        self.external_window.connect("window-state-event", self.minimize_external_window)
        self.current_tab = None
        self.is_using_external_window = False
        builder.connect_signals(self)

    def add_tab(self, tab: "AbstractTab"):
        self.tabs.append(tab)
        self.notebook.append_page(tab.tab_widget, Gtk.Label(label=tab.name))

    def library_updated(self, fc_button):
        new_lib = load_motor_library(Path(fc_button.get_filename()))
        for tab in self.tabs:
            tab.update_library(new_lib)

    def _pdf_viewer_not_available(self, path):
        dialog = Gtk.Dialog(parent=self.window)
        dialog.add_button("Ok", 0)
        lab = Gtk.Label()
        lab.set_markup("<big>Oh no - PDF files cannot be opened in docker :( You can find this doc at:</big>")
        dialog.vbox.add(lab)

        ent = Gtk.Entry()
        ent.set_text(path)
        ent.set_editable(False)
        dialog.vbox.add(ent)
        dialog.vbox.set_spacing(10)

        dialog.set_size_request(800, -1)
        dialog.show_all()
        dialog.run()
        dialog.destroy()

    def show_math_doc(self, *args):
        if sys.platform == 'linux':
            try:
                subprocess.call(["xdg-open", get_doc_path("BrushlessMotorPhysics.pdf")])
            except FileNotFoundError:
                self._pdf_viewer_not_available(get_doc_path("BrushlessMotorPhysics.pdf"))
        else:
            os.startfile(get_doc_path("BrushlessMotorPhysics.pdf"))

    def show_user_manual(self, *args):
        if sys.platform == 'linux':
            try:
                subprocess.call(["xdg-open", get_doc_path("user_manual.pdf")])
            except FileNotFoundError:
                self._pdf_viewer_not_available(get_doc_path("user_manual.pdf"))
        else:
            os.startfile(get_doc_path("user_manual.pdf"))

    def switch_plot_window(self, widget, state):
        self.is_using_external_window = state
        if self.is_using_external_window:
            self.move_current_tab_plot_to_window()
            self.external_window.show_all()
        else:
            self.return_plot_to_current_tab()
            self.external_window.hide()

    def move_current_tab_plot_to_window(self):
        self.current_tab.tab_widget.remove(self.current_tab.scroll_widget)
        self.external_window.add(self.current_tab.scroll_widget)

    def return_plot_to_current_tab(self):
        self.external_window.remove(self.current_tab.scroll_widget)
        self.current_tab.tab_widget.pack2(self.current_tab.scroll_widget, True, False)

    def change_tab(self, notebook, page, page_num):
        # If using external window, rearrange widgets
        if self.is_using_external_window:
            self.return_plot_to_current_tab()
            self.current_tab = self.tabs[page_num]
            self.move_current_tab_plot_to_window()
        self.current_tab = self.tabs[page_num]

    def minimize_external_window(self, widget, event):
        if self.is_using_external_window:
            if event.new_window_state & Gdk.WindowState.ICONIFIED > 0:
                self.switch_external_window.set_state(False)
                self.external_window.deiconify()

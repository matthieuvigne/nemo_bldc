import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk

from .gui.gui_compare_motors import CompareMotors
from .gui.gui_single_motor_perf import SingleMotorPerfTab
from .gui.gui_simulation import SimulateMotor
from .gui.main_window import MainWindow

from .ressources import DEFAULT_LIBRARY
import pkg_resources


def nemo_main(is_unit_test=False):
    version = pkg_resources.require("nemo_bldc")[0].version

    style_provider = Gtk.CssProvider()
    css = b"""
    progress, trough {
        min-height: 20px;
    }
    """
    style_provider.load_from_data(css)
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(),
        style_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

    main = MainWindow(version)
    main.window.connect("delete-event", Gtk.main_quit)
    main.window.set_default_size(400, 300)

    c_tab = CompareMotors()
    main.add_tab(c_tab)
    main.add_tab(SingleMotorPerfTab())
    main.add_tab(SimulateMotor())
    for tab in main.tabs:
        tab.update_library(DEFAULT_LIBRARY)
    c_tab.add_motor()

    main.window.show_all()
    for t in main.tabs:
        t.user_asked_for_update()
    if not is_unit_test:
        Gtk.main()


if __name__ == "__main__":
    nemo_main()

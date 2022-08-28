import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from .gui.gui_compare_motors import CompareMotors
from .gui.gui_single_motor_perf import SingleMotorPerfTab
from .gui.main_window import MainWindow

from .ressources import DEFAULT_LIBRARY
import pkg_resources

def nemo_main(is_unit_test = False):
    main = MainWindow()
    main.window.connect("delete-event", Gtk.main_quit)
    main.window.set_default_size(400, 300)

    c_tab = CompareMotors()
    main.add_tab(c_tab)
    main.add_tab(SingleMotorPerfTab())
    for tab in main.tabs:
        tab.update_library(DEFAULT_LIBRARY)
    c_tab.add_motor()

    version = pkg_resources.require("nemo_bldc")[0].version
    main.window.set_title(f"Nemo - {version}")
    main.window.show_all()
    if is_unit_test:
        for t in main.tabs:
            t.update_plot()
    else:
        Gtk.main()

if __name__ == "__main__":
    nemo_main()



# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Test slideshow.py for vimiv's test suite."""

from unittest import main

from gi import require_version
require_version("Gtk", "3.0")
from gi.repository import Gtk

from vimiv_testcase import VimivTestCase


def refresh_gui(vimiv=None):
    """Refresh the GUI as the Gtk.main() loop is not running when testing.

    Args:
        vimiv: Vimiv class to receive slideshow index.
    """
    current_pos = vimiv.index
    while current_pos == vimiv.index:
        Gtk.main_iteration_do(False)


class SlideshowTest(VimivTestCase):
    """Slideshow Tests."""

    @classmethod
    def setUpClass(cls):
        cls.init_test(cls, ["vimiv/testimages/arch_001.jpg"])
        cls.slideshow = cls.vimiv["slideshow"]

    def test_toggle(self):
        """Toggle slideshow."""
        self.assertFalse(self.slideshow.running)
        self.slideshow.toggle()
        self.assertTrue(self.slideshow.running)
        self.slideshow.toggle()
        self.assertFalse(self.slideshow.running)
        # Throw some errors
        self.vimiv["thumbnail"].toggled = True
        self.slideshow.toggle()
        self.assertFalse(self.slideshow.running)
        self.vimiv["thumbnail"].toggled = False
        paths_before = self.vimiv.paths
        self.vimiv.paths = []
        self.slideshow.toggle()
        self.assertFalse(self.slideshow.running)
        self.vimiv.paths = paths_before

    def test_set_delay(self):
        """Set slideshow delay."""
        self.assertEqual(self.slideshow.delay, 2.0)
        self.slideshow.set_delay("3.0")
        self.assertEqual(self.slideshow.delay, 3.0)
        self.slideshow.set_delay(None, "-0.2")
        self.assertEqual(self.slideshow.delay, 2.8)
        self.slideshow.set_delay(None, "+0.4")
        self.assertAlmostEqual(self.slideshow.delay, 3.2)
        # Shrink with num_str
        self.vimiv["eventhandler"].num_str = "2"
        self.slideshow.set_delay(None, "-0.2")
        self.assertAlmostEqual(self.slideshow.delay, 2.8)
        # Set via toggle
        self.vimiv["eventhandler"].num_str = "2"
        self.slideshow.toggle()
        self.assertEqual(self.slideshow.delay, 2.0)
        # Set to a too small value
        self.slideshow.set_delay("0.1")
        self.assertEqual(self.slideshow.delay, 0.5)
        ##################
        #  Command line  #
        ##################
        # Increase by value
        self.run_command("slideshow_delay 03")
        self.assertEqual(self.slideshow.delay, 0.8)
        # Fail because of invalid argument
        self.run_command("slideshow_delay value")
        self.check_statusbar("ERROR: Argument for delay must be of type float")
        # Set to default
        self.run_command("set slideshow_delay")
        self.assertEqual(self.slideshow.delay, self.slideshow.default_delay)
        # Fail because of invalid argument
        self.run_command("set slideshow_delay value")
        self.check_statusbar("ERROR: Argument for delay must be of type float")

    def test_running(self):
        """Check if slideshow runs correctly."""
        self.assertEqual(self.vimiv.index, 0)
        self.slideshow.toggle()
        # Set delay when running
        self.slideshow.set_delay("0.5")
        self.assertEqual(self.slideshow.delay, 0.5)
        for i in range(1, 3):
            refresh_gui(self.vimiv)
            self.assertEqual(self.vimiv.index, i)
        refresh_gui(self.vimiv)

    def tearDown(self):
        if self.slideshow.running:
            self.slideshow.toggle()
        self.slideshow.delay = 2.0


if __name__ == "__main__":
    main()

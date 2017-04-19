# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Test the Information class for vimiv's test suite."""

from unittest import main

from vimiv_testcase import VimivTestCase


class InformationTest(VimivTestCase):
    """Information Tests.

    The pop-up tests simply run through the pop-ups not checking for anything.
    If all attributes are set correctly, not much can go wrong.
    """

    @classmethod
    def setUpClass(cls):
        cls.init_test(cls)

    def test_print_version(self):
        """Print version information to screen."""
        version = self.vimiv["information"].get_version()
        self.assertIn("0.9.0.dev0", version)

    def test_show_version_info(self):
        """Show the version info pop-up."""
        self.vimiv["information"].show_version_info(True)

    def test_show_licence(self):
        """Show the licence pop-up."""
        self.vimiv["information"].show_licence(None, True)


if __name__ == "__main__":
    main()

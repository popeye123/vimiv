# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Test library.py for vimiv's test suite."""

import os
from unittest import main

from gi import require_version
require_version("Gtk", "3.0")
from gi.repository import Gtk

from vimiv_testcase import VimivTestCase


class LibraryTest(VimivTestCase):
    """Test Library."""

    @classmethod
    def setUpClass(cls):
        cls.init_test(cls, ["vimiv/testimages/"])
        cls.lib = cls.vimiv["library"]

    def test_toggle(self):
        """Toggle the library."""
        self.lib.toggle()
        self.assertFalse(self.lib.treeview.is_focus())
        self.lib.toggle()
        self.assertTrue(self.lib.treeview.is_focus())

    def test_toggle_with_slideshow(self):
        """Toggle the library with running slideshow."""
        self.lib.toggle()
        self.vimiv["slideshow"].toggle()
        self.lib.toggle()
        self.assertFalse(self.vimiv["slideshow"].running)
        self.assertTrue(self.lib.treeview.is_focus())

    def test_file_select(self):
        """Select file in library."""
        # Directory by position
        path = Gtk.TreePath([self.lib.files.index("directory")])
        self.lib.file_select(None, path, None, False)
        self.assertEqual(self.lib.files, ["symlink with spaces .jpg"])
        self.lib.move_up()
        # Library still focused
        self.assertTrue(self.lib.treeview.is_focus())
        # Image by position closing library
        path = Gtk.TreePath([self.lib.files.index("arch_001.jpg")])
        self.lib.file_select(None, path, None, True)
        expected_images = ["arch-logo.png", "arch_001.jpg", "symlink_to_image",
                           "vimiv.bmp", "vimiv.svg", "vimiv.tiff"]
        expected_images = [os.path.abspath(image) for image in expected_images]
        self.assertEqual(self.vimiv.paths, expected_images)
        open_image = self.vimiv.paths[self.vimiv.index]
        expected_image = os.path.abspath("arch_001.jpg")
        self.assertEqual(expected_image, open_image)
        # Library closed, image has focus
        self.assertFalse(self.lib.treeview.is_focus())
        self.assertFalse(self.lib.grid.is_focus())
        self.assertTrue(self.vimiv["image"].scrolled_win.is_focus())

    def test_move_pos(self):
        """Move position in library."""
        # G
        self.assertEqual(self.vimiv.get_pos(True), "animation")
        self.lib.move_pos()
        self.assertEqual(self.vimiv.get_pos(True), "vimiv.tiff")
        # 3g
        self.vimiv["eventhandler"].num_str = "3"
        self.lib.move_pos()
        self.assertEqual(self.vimiv.get_pos(True), "arch_001.jpg")
        self.assertFalse(self.vimiv["eventhandler"].num_str)
        # g
        self.lib.move_pos(False)
        self.assertEqual(self.vimiv.get_pos(True), "animation")
        # Throw an error
        self.vimiv["eventhandler"].num_str = "300"
        self.lib.move_pos()
        self.assertEqual(self.vimiv.get_pos(True), "animation")
        self.check_statusbar("WARNING: Unsupported index")

    def test_resize(self):
        """Resize library."""
        # Set to 200
        self.lib.resize(None, True, "200")
        self.assertEqual(200,
                         self.lib.scrollable_treeview.get_size_request()[0])
        # Grow
        self.lib.resize(True)
        self.assertEqual(220,
                         self.lib.scrollable_treeview.get_size_request()[0])
        self.lib.resize(True, False, "30")
        self.assertEqual(250,
                         self.lib.scrollable_treeview.get_size_request()[0])
        # Shrink
        self.lib.resize(False, False, "50")
        self.assertEqual(200,
                         self.lib.scrollable_treeview.get_size_request()[0])
        # Grow via num_str
        self.vimiv["eventhandler"].num_str = "2"
        self.lib.resize(True)
        self.assertEqual(240,
                         self.lib.scrollable_treeview.get_size_request()[0])
        self.vimiv["eventhandler"].num_str = "2"
        self.lib.resize(False)
        self.assertEqual(200,
                         self.lib.scrollable_treeview.get_size_request()[0])
        self.assertFalse(self.vimiv["eventhandler"].num_str)
        # Too small
        self.lib.resize(False, False, "500")
        self.assertEqual(100,
                         self.lib.scrollable_treeview.get_size_request()[0])
        # Throw errors
        self.lib.resize(False, False, "hi")
        self.check_statusbar("ERROR: Library width must be an integer")
        self.lib.resize(False, True, "hi")
        self.check_statusbar("ERROR: Library width must be an integer")
        ##################
        #  Command line  #
        ##################
        # Default 20
        self.run_command("grow_lib")
        self.assertEqual(120,
                         self.lib.scrollable_treeview.get_size_request()[0])
        # Value passed
        self.run_command("grow_lib 30")
        self.assertEqual(150,
                         self.lib.scrollable_treeview.get_size_request()[0])
        # Fail by passing an invalid value
        self.run_command("grow_lib value")
        self.check_statusbar("ERROR: Library width must be an integer")
        # Set width to default
        self.run_command("set library_width")
        self.assertEqual(self.lib.default_width,
                         self.lib.scrollable_treeview.get_size_request()[0])
        # Fail by passing an invalid value
        self.run_command("set library_width value")
        self.check_statusbar("ERROR: Library width must be an integer")

    def test_scroll(self):
        """Scroll library."""
        # j
        self.assertEqual(self.vimiv.get_pos(True), "animation")
        self.lib.scroll("j")
        self.assertEqual(self.vimiv.get_pos(True), "arch-logo.png")
        # k
        self.lib.scroll("k")
        self.assertEqual(self.vimiv.get_pos(True), "animation")
        # 3j
        self.vimiv["eventhandler"].num_str = "3"
        self.lib.scroll("j")
        self.assertEqual(self.vimiv.get_pos(True), "directory")
        self.assertFalse(self.vimiv["eventhandler"].num_str)
        # l
        expected_path = os.path.abspath("directory")
        self.lib.scroll("l")
        self.assertEqual(self.lib.files, ["symlink with spaces .jpg"])
        self.assertEqual(expected_path, os.getcwd())
        # h
        expected_path = os.path.abspath("..")
        self.lib.scroll("h")
        self.assertEqual(expected_path, os.getcwd())
        # Remember pos
        self.assertEqual(self.vimiv.get_pos(True), "directory")
        # Back to beginning
        self.vimiv["eventhandler"].num_str = "3"
        self.lib.scroll("k")
        self.assertEqual(self.vimiv.get_pos(True), "animation")
        # Fail because of invalid argument
        self.lib.scroll("o")
        self.check_statusbar("ERROR: Invalid scroll direction o")

    def test_display_symlink(self):
        """Show real path of symbolic links in library as well."""
        index = self.lib.files.index("symlink_to_image")
        model = self.lib.treeview.get_model()
        markup_string = model[index][1]
        expected_string = "symlink_to_image  →  " \
            + os.path.realpath("symlink_to_image")
        self.assertEqual(markup_string, expected_string)
        # Also after a search
        self.vimiv["commandline"].cmd_search()
        self.vimiv["commandline"].reset_text()
        markup_string = model[index][1]
        expected_string = "symlink_to_image  →  " \
            + os.path.realpath("symlink_to_image")
        self.assertEqual(markup_string, expected_string)

    def test_broken_symlink(self):
        """Reload library with broken symlink."""
        tmpfile = "temporary.png"
        sym = "broken_sym"
        os.system("cp arch-logo.png " + tmpfile)
        os.system("ln -s " + tmpfile + " " + sym)
        os.remove(tmpfile)
        self.lib.reload(".")
        self.assertNotIn(sym, self.lib.files)
        os.remove(sym)

    def test_move_up(self):
        """Move up into directory."""
        before = os.getcwd()
        expected = "/".join(before.split("/")[:-2])
        self.vimiv["eventhandler"].num_str = "2"
        self.lib.move_up()
        self.assertEqual(os.getcwd(), expected)
        self.lib.move_up(before)
        self.assertEqual(os.getcwd(), before)

    def tearDown(self):
        # Reopen and back to beginning
        if not self.lib.treeview.is_visible():
            self.lib.toggle()
        self.lib.treeview.set_cursor([Gtk.TreePath(0)], None, False)


if __name__ == "__main__":
    main()

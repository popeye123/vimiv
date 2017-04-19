# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""Deal with the handling of tags for vimiv."""

import os

from gi.repository import Gtk, GLib

from vimiv.app_component import AppComponent
from vimiv.fileactions import populate
from vimiv.helpers import read_file, error_message


class TagHandler(AppComponent):
    """Handle tags.

    Attributes:
        app: The main vimiv application to interact with.
        directory: Directory in which tags are stored.
        last: Last tag that was loaded.
    """

    def __init__(self, app):
        """Create the necessary objects.

        Args:
            app: The main vimiv application to interact with.
        """
        super().__init__(app)
        self.app = app
        # Create tags directory
        self.directory = os.path.join(GLib.get_user_data_dir(), "vimiv", "Tags")
        os.makedirs(self.directory, exist_ok=True)
        # If there are tags in the old location, move them to the new one
        # TODO remove this in a new version, assigned for 0.10
        old_directory = os.path.expanduser("~/.vimiv/Tags")
        if os.path.isdir(old_directory):
            old_tags = os.listdir(old_directory)
            for f in old_tags:
                old_path = os.path.join(old_directory, f)
                new_path = os.path.join(self.directory, f)
                os.rename(old_path, new_path)
            message = "Moved tags from the old directory %s " \
                "to the new location %s." % (old_directory, self.directory)
            error_message(message, running_tests=self.app.running_tests)
            os.rmdir(old_directory)
        self.last = ""

    def read(self, tagname):
        """Read a tag and return the images in it.

        Args:
            tagname: Name of tag to operate on.

        Return:
            List of images in the tag called tagname.
        """
        tagfile_name = os.path.join(self.directory, tagname)
        tagged_images = read_file(tagfile_name)
        return tagged_images

    def write(self, imagelist, tagname):
        """Add a list of images to a tag.

        Args:
            imagelist: List of images to write to the tag.
            tagname: Name of tag to operate on.
        """
        # Backup required for tests
        imagelist = imagelist if imagelist else self.app["mark"].marked
        tagfile_name = os.path.join(self.directory, tagname)
        tagged_images = self.read(tagname)
        with open(tagfile_name, "a") as tagfile:
            for image in imagelist:
                if image not in tagged_images:
                    tagfile.write(image + "\n")

    def remove(self, tagname):
        """Remove a tag showing an error if the tag doesn't exist.

        Args:
            tagname: Name of tag to operate on.
        """
        tagfile_name = os.path.join(self.directory, tagname)
        if os.path.isfile(tagfile_name):
            os.remove(tagfile_name)
        else:
            err = "Tagfile '%s' does not exist" % (tagname)
            self.app["statusbar"].message(err, "error")

    def load(self, tagname):
        """Load all images in a tag as current filelist.

        Args:
            tagname: Name of tag to operate on.
        """
        os.chdir(self.directory)
        # Read file and get all tagged images as list
        tagged_images = self.read(tagname)
        # Populate filelist
        self.app.paths = []
        self.app.paths = populate(tagged_images)[0]
        if self.app.paths:
            self.app["image"].scrolled_win.show()
            self.app["library"].scrollable_treeview.set_hexpand(False)
            self.app["image"].load_image()
            # Focus in library if it is open
            if self.app["library"].grid.is_visible():
                self.app["library"].reload(self.directory)
                tag_pos = self.app["library"].files.index(tagname)
                self.app["library"].treeview.set_cursor(Gtk.TreePath(tag_pos),
                                                        None, False)
            # Remember last tag selected
            self.last = tagname
        else:
            message = "Tagfile '%s' has no valid images" % (tagname)
            self.app["statusbar"].message(message, "error")
            self.last = ""

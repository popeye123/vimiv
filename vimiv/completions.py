# vim: ft=python fileencoding=utf-8 sw=4 et sts=4
"""The commandline completion for vimiv."""

import os
import re
from itertools import takewhile
from string import digits

from gi.repository import Gtk

from vimiv.app_component import AppComponent
from vimiv.fileactions import is_image
from vimiv.helpers import listdir_wrapper, read_info_from_man


class Completion(AppComponent):
    """Completion for vimiv's commandline.

    Attributes:
        app: The main vimiv application to interact with.
        liststores: Dictionary containing the liststore models for different
            completion types.
        entry: The commandline entry.
        info: ScrolledWindow containing the completion information.
        tab_position: Position when tabbing through completion elements.
        tab_presses: Amount of tab presses.
        prefixed_digits: User prefixed digits for internal command.
    """

    def __init__(self, app):
        """Create the necessary objects and settings.

        Args:
            app: The main vimiv application to interact with.
        """
        super().__init__(app)
        self.app = app
        # Create liststore dictionary with the filter used.
        self.liststores = {"internal": [Gtk.ListStore(str, str)],
                           "external": [Gtk.ListStore(str, str)],
                           "path": [Gtk.ListStore(str, str)],
                           "tag": [Gtk.ListStore(str, str)],
                           "search": [Gtk.ListStore(str, str)],
                           "trash": [Gtk.ListStore(str, str)]}
        for liststore in self.liststores.values():
            comp_filter = liststore[0].filter_new()
            comp_filter.set_visible_func(self.completion_filter)
            liststore.append(comp_filter)
        # Use the commandline entry here and connect to the refilter method
        self.entry = self.app["commandline"].entry
        self.entry.connect("changed", self.refilter)
        # Create treeview
        self.treeview = Gtk.TreeView()
        self.treeview.set_enable_search(False)
        self.treeview.set_headers_visible(False)
        self.treeview.set_activate_on_single_click(True)
        padding = self.app.settings["GENERAL"]["commandline_padding"]
        renderer = Gtk.CellRendererText()
        renderer.set_padding(padding, 0)
        command_column = Gtk.TreeViewColumn("Command", renderer, markup=0)
        command_column.set_expand(True)
        self.treeview.append_column(command_column)
        info_column = Gtk.TreeViewColumn("Info", renderer, markup=1)
        self.treeview.append_column(info_column)
        self.treeview.connect("row-activated", self.activate)
        # Scrolled window for the completion info
        self.info = Gtk.ScrolledWindow()
        self.info.set_size_request(
            10, self.app.settings["GENERAL"]["completion_height"])
        self.info.add(self.treeview)
        # Defaults
        self.tab_position = 0
        self.tab_presses = 0
        self.prefixed_digits = ""

    def complete(self, inverse=False):
        """Run completion.

        Try to enter the best matching completion into the entry. On more than
        one tab start to run through the possible completions.

        Args:
            inverse: If True, tabbing backwards.
        """
        maximum = len(self.treeview.get_model())
        # If we have no entries, completing makes no sense
        if not maximum:
            return
        # Try to set best match first
        elif not self.tab_presses:
            best_match = ":" + self.prefixed_digits
            comp_type = self.get_comp_type()
            liststore = self.liststores[comp_type][1]
            first = str(liststore[0][0])
            last = str(liststore[-1][0])
            for i, char in enumerate(first):
                if char == last[i]:
                    best_match += char
                else:
                    break
            if best_match != self.entry.get_text():
                self.entry.set_text(best_match)
                self.entry.set_position(-1)
                return
            # Start at the last element with Shift+Tab
            elif inverse:
                self.tab_position = -1
        # Set position according to direction and move
        elif inverse:
            self.tab_position -= 1
        else:
            self.tab_position += 1
        self.tab_presses += 1
        self.tab_position %= maximum
        self.treeview.set_cursor(Gtk.TreePath(self.tab_position), None, False)
        self.treeview.scroll_to_cell(Gtk.TreePath(self.tab_position),
                                     None, True, 0.5, 0)
        return True  # Deactivate default keybinding (here for Tab)

    def show(self):
        """Show the completion information."""
        # Hacky way to not show the last selected item
        self.treeview.set_model(Gtk.ListStore(str, str))
        self.refilter(self.entry)
        self.info.show()

    def hide(self):
        """Hide the completion information."""
        self.info.hide()

    def activate(self, treeview, path, column):
        """Enter the completion text of the treeview into the commandline.

        Args:
            treeview: TreeView that was activated.
            path: Activated TreePath.
            column: Activated TreeViewColumn.
        """
        if treeview:
            count = path.get_indices()[0]
            self.entry.grab_focus()
        else:
            count = self.tab_position
        comp_type = self.get_comp_type()
        row = self.liststores[comp_type][1][count]
        self.entry.set_text(":" + self.prefixed_digits + row[0])
        self.entry.set_position(-1)

    def get_comp_type(self, command=""):
        """Get the current completion type depending on command.

        Args:
            command: The command to check completion type for. If there is none,
                default to getting the text from self.entry.
        Return:
            The completion type to use.
        """
        if not command:
            command = self.entry.get_text()
        if command and command[0] != ":":
            return "search"
        command = command.lstrip(":")
        # Nothing entered -> checks are useless
        if command:
            # External commands are prefixed with an !
            if command[0] == "!":
                return "external"
            # Paths are prefixed with a /
            elif command[0] in ["/", ".", "~"]:
                return "path"
            # Tag commands
            elif re.match(r'^(tag_(write|remove|load) )', command):
                return "tag"
            # Undelete files from trash
            elif command.startswith("undelete"):
                return "trash"
        return "internal"

    def complete_path(self, path):
        """Complete paths.

        Args:
            path: (Partial) name of the path to run completion on.
        Return:
            List containing formatted matching paths.
        """
        self.liststores["path"][0].clear()
        # Directory of the path, default to .
        directory = os.path.dirname(path) if os.path.dirname(path) else path
        if not os.path.exists(os.path.expanduser(directory)) \
                or not os.path.isdir(os.path.expanduser(directory)):
            directory = "."
        # /dev causes havoc
        if directory == "/dev":
            return
        # Files in that directory
        files = listdir_wrapper(directory, self.app["library"].show_hidden)
        # Format them neatly depending on directory and type
        for fil in files:
            fil = os.path.join(directory, fil)
            # Directory
            if os.path.isdir(os.path.expanduser(fil)):
                self.liststores["path"][0].append([fil + "/", ""])
            # Acceptable file
            elif is_image(fil):
                self.liststores["path"][0].append([fil, ""])

    def complete_tag(self, command):
        """Append the available tag names to an internal tag command.

        Args:
            command: The internal command to complete.
        """
        self.liststores["tag"][0].clear()
        tags = listdir_wrapper(self.app["tags"].directory,
                               self.app["library"].show_hidden)
        for tag in tags:
            self.liststores["tag"][0].append([command.split()[0] + " " + tag,
                                              ""])

    #  The function currently only hides the commandline but is implemented
    #  for possible future usage.
    def complete_search(self):
        """Hide the info as it has no use in search."""
        self.info.hide()

    def complete_external(self, command):
        """If there is more than one word in command, do path completion.

        Args:
            command: The internal command to complete.
        """
        self.liststores["external"][0].clear()
        command = command.lstrip("!").lstrip(" ")
        spaces = command.count(" ")
        # If there are spaces, path completion for external commands makes sense
        if spaces:
            args = command.split()
            # Last argument is the path to complete
            if len(args) > spaces:
                path = args[-1]
                # Do not try path completion for arguments
                if path.startswith("-"):
                    self.info.hide()
                    return
                command = " ".join(args[:-1]) + " "
            else:
                path = "./"
            self.complete_path(path)
            # Prepend command to path completion
            # Gtk ListStores are iterable
            # pylint:disable=not-an-iterable
            for row in self.liststores["path"][0]:
                match = "!" + command + re.sub(r'^\./', "", row[0])
                self.liststores["external"][0].append([match, ""])
        else:
            self.info.hide()

    def complete_trash(self, command):
        """Complete files in trash directory for :undelete.

        Args:
            command: The internal command to complete.
        """
        # Get files in trash directory
        self.liststores["trash"][0].clear()
        trash_directory = \
            self.app["manipulate"].trash_manager.get_files_directory()
        trash_files = sorted(os.listdir(trash_directory))
        # Add them to completion formatted to 'undelete $FILE'
        for fil in trash_files:
            # Ensure we only complete image files as vimiv is not meant as a
            # general trash tool but provides this for convenience
            abspath = os.path.join(trash_directory, fil)
            if is_image(abspath):
                completion = "undelete %s" % (fil)
                self.liststores["trash"][0].append([completion, ""])

    def generate_commandlist(self):
        """Generate a list of internal vimiv commands and store it."""
        commands = [cmd for cmd in self.app["commands"]
                    if not self.app["commands"][cmd]["is_hidden"]]
        aliases = list(self.app.aliases.keys())
        all_commands = sorted(commands + aliases)
        infodict = read_info_from_man()
        for command in all_commands:
            if command in infodict:
                info = infodict[command]
            elif command in self.app.aliases:
                info = "Alias to " + self.app.aliases[command]
                # Escape ampersand for Gtk
                info = info.replace("&", "&amp;")
            else:
                info = ""
            info = "<i>" + info + "</i>"
            self.liststores["internal"][0].append([command, info])

    def completion_filter(self, model, treeiter, data):
        """Filter function used in the liststores to filter completions.

        Args:
            model: The liststore model to filter.
            treeiter: The TreeIter representing a row in the model.
            data: User appended data, here the completion mode.
        Return:
            True for a match, False else.
        """
        command = self.entry.get_text().lstrip(":")
        # Allow number prefixes
        self.prefixed_digits = "".join(takewhile(str.isdigit, command))
        command = command.lstrip(digits)
        return model[treeiter][0].startswith(command)

    def refilter(self, entry):
        """Refilter the completion list according to the text in entry."""
        # Replace multiple spaces with single space
        entry.set_text(re.sub(r' +', " ", entry.get_text()))
        comp_type = self.get_comp_type()
        command = entry.get_text().lstrip(":")
        if command:
            self.info.show()
        if comp_type == "path":
            self.complete_path(command)
        elif comp_type == "tag":
            self.complete_tag(command)
        elif comp_type == "search":
            self.complete_search()
        elif comp_type == "external":
            self.complete_external(command)
        elif comp_type == "trash":
            self.complete_trash(command)
        self.treeview.set_model(self.liststores[comp_type][1])
        self.liststores[comp_type][1].refilter()
        self.reset()

    def reset(self):
        """Reset all internal counts."""
        self.tab_position = 0
        self.tab_presses = 0

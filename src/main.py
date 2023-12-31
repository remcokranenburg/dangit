# main.py
#
# Copyright 2023 Remco Kranenburg
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import sys
import gi
from pathlib import Path

gi.require_version('Gtk', '4.0')
gi.require_version('GtkSource', '5')
gi.require_version('Adw', '1')

from gi.repository import GLib, GObject, Gtk, Gio, Adw, GtkSource
from .window import DangitWindow


class DangitApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self):
        super().__init__(application_id='com.remcokranenburg.Dangit',
                         flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        GtkSource.init()
        GObject.type_register(GtkSource.View)
        self.create_action('open-project', self.on_open_project_action, ['<primary>o'])
        self.create_action('open-folder', self.on_open_folder_action)
        self.create_action('quit', lambda *_: self.quit(), ['<primary>q'])
        self.create_action('about', self.on_about_action)
        self.create_action('preferences', self.on_preferences_action)

    def do_activate(self):
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        win = self.props.active_window
        if not win:
            win = DangitWindow(application=self)
        win.present()

    def on_open_project_action(self, wiget, _):
        """Callback for the app.open-project action."""
        self.props.active_window.stack.set_visible_child_name("projects")

    def on_open_folder_action(self, widget, _):
        """Callback for the app.open-folder action."""

        def on_selected(dialog, result):
            try:
                folder = dialog.select_folder_finish(result)
                children = Gtk.DirectoryList.new("standard::display-name", folder)
                selection_model = Gtk.SingleSelection.new(children)

                for f in ["README.md", "README.txt", "README"]:
                    file = folder.get_child(f)

                    if file.query_exists():
                        buffer = self.props.active_window.editor.get_buffer()
                        source_file = GtkSource.File(location=file)
                        loader = GtkSource.FileLoader.new(buffer, source_file)
                        loader.load_async(GLib.PRIORITY_DEFAULT, None, None, None, None, None)
                        break

                def on_selected_file(selection, *_):
                    selected_item = selection.get_selected_item()
                    selected_file = selected_item.get_attribute_object("standard::file")
                    buffer = self.props.active_window.editor.get_buffer()
                    source_file = GtkSource.File(location=selected_file)
                    loader = GtkSource.FileLoader.new(buffer, source_file)
                    loader.load_async(GLib.PRIORITY_DEFAULT, None, None, None, None, None)

                selection_model.connect("selection_changed", on_selected_file)
                self.props.active_window.files.set_model(selection_model)
                self.props.active_window.stack.set_visible_child_name("editor")

            except GLib.GError as e:
                print("Nothing selected")

        directory = Gio.File.new_for_path("/")
        dialog = Gtk.FileDialog(initial_folder=directory)
        dialog.select_folder(self.props.active_window, None, on_selected)

    def on_about_action(self, widget, _):
        """Callback for the app.about action."""
        about = Adw.AboutWindow(transient_for=self.props.active_window,
                                application_name='Dangit!',
                                application_icon='com.remcokranenburg.Dangit',
                                developer_name='Remco Kranenburg',
                                version='0.1.0',
                                developers=['Remco Kranenburg'],
                                copyright='© 2023 Remco Kranenburg')
        about.present()

    def on_preferences_action(self, widget, _):
        """Callback for the app.preferences action."""
        print('app.preferences action activated')

    def create_action(self, name, callback, shortcuts=None):
        """Add an application action.

        Args:
            name: the name of the action
            callback: the function to be called when the action is
              activated
            shortcuts: an optional list of accelerators
        """
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)


def main(version):
    """The application's entry point."""
    app = DangitApplication()
    return app.run(sys.argv)

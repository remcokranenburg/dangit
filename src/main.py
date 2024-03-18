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

gi.require_version("Gtk", "4.0")
gi.require_version("GtkSource", "5")
gi.require_version("Adw", "1")

from gi.repository import GObject, Gio, Adw, Gtk, GtkSource

from dangit.window import DangitWindow


class DangitApplication(Adw.Application):
    """The main application singleton class."""

    version: str
    projects: Gio.ListStore
    recent_manager: Gtk.RecentManager

    def __init__(self):
        super().__init__(
            application_id="com.remcokranenburg.Dangit", flags=Gio.ApplicationFlags.DEFAULT_FLAGS
        )
        GtkSource.init()
        GObject.type_register(GtkSource.View)
        self.create_action("open-project", self.on_open_project_action, ["<primary>o"])
        self.create_action("quit", lambda *_: self.quit(), ["<primary>q"])
        self.create_action("close", lambda *_: self.props.active_window.close(), ["<primary>w"])
        self.create_action("about", self.on_about_action)
        self.create_action("preferences", self.on_preferences_action)

        self.version = "unknown"
        self.projects = Gio.ListStore.new(Gio.File)
        self.recent_manager = Gtk.RecentManager.get_default()

    def do_activate(self):
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        win = self.props.active_window
        if not win:
            win = DangitWindow(
                projects=self.projects, recent_manager=self.recent_manager, application=self
            )
        win.present()

    def on_open_project_action(self, widget, _):
        """Callback for the app.open-project action."""
        win = DangitWindow(
            projects=self.projects, recent_manager=self.recent_manager, application=self
        )
        win.present()

    def on_about_action(self, widget, _):
        """Callback for the app.about action."""
        about = Adw.AboutWindow(
            transient_for=self.props.active_window,
            application_name="Dangit!",
            application_icon="com.remcokranenburg.Dangit",
            developer_name="Remco Kranenburg",
            version=self.version,
            developers=["Remco Kranenburg"],
            copyright="© 2023 Remco Kranenburg",
        )
        about.present()

    def on_preferences_action(self, widget, _):
        """Callback for the app.preferences action."""
        print("app.preferences action activated")

    def create_action(self, name: str, callback, shortcuts=None):
        """Add an application action

        Args:
            name: the name of the action
            callback: called when the action is activated
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
    app.version = version
    return app.run(sys.argv)

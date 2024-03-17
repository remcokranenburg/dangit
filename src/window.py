# window.py
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

from gi.repository import Adw, Gio, Gtk, GtkSource, GLib

@Gtk.Template(resource_path='/com/remcokranenburg/Dangit/window.ui')
class DangitWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'DangitWindow'

    # ui elements
    stack: Gtk.Stack = Gtk.Template.Child()
    editor: GtkSource.View = Gtk.Template.Child()
    files: Gtk.ListView = Gtk.Template.Child()

    # project data
    buffer: GtkSource.Buffer

    # theming
    language_manager: GtkSource.LanguageManager
    style_scheme_manager: GtkSource.StyleSchemeManager

    def set_editor_style(self, settings, *_):
        if settings.get_property("gtk-application-prefer-dark-theme"):
            self.buffer.set_style_scheme(self.style_scheme_manager.get_scheme('classic-dark'))
        else:
            self.buffer.set_style_scheme(self.style_scheme_manager.get_scheme('classic'))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.buffer = self.editor.get_buffer()
        self.language_manager = GtkSource.LanguageManager.get_default()
        self.style_scheme_manager = GtkSource.StyleSchemeManager.get_default()

        self.create_action('open-folder', self.on_open_folder_action)

        self.editor.set_smart_backspace(True)
        self.editor.set_show_line_marks(True)

        app_settings = Gio.Settings.new('com.remcokranenburg.Dangit')

        # set initial values
        self.set_property("maximized", app_settings.get_boolean("window-maximized"))
        self.set_property("default-width", app_settings.get_int("window-width"))
        self.set_property("default-height", app_settings.get_int("window-height"))

        # update settings when window is resized
        app_settings.bind("window-maximized", self, "maximized", Gio.SettingsBindFlags.SET)
        app_settings.bind("window-width", self, "default-width", Gio.SettingsBindFlags.SET)
        app_settings.bind("window-height", self, "default-height", Gio.SettingsBindFlags.SET)

        os_settings = Gtk.Settings.get_default()
        os_settings.connect("notify::gtk-application-prefer-dark-theme", self.set_editor_style)
        self.set_editor_style(os_settings)

        provider = Gtk.CssProvider()
        provider.load_from_data("textview { font-family: Monospace; }")
        style_context = self.editor.get_style_context()
        style_context.add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        def on_bind(self, list_item):
            box = list_item.get_child()
            label = box.get_first_child()
            model = list_item.get_item()
            label.set_label(model.get_display_name())

        def on_setup(self, list_item):
            box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
            box.append(Gtk.Label.new())
            list_item.set_child(box)

        factory = Gtk.SignalListItemFactory.new()
        factory.connect("bind", on_bind)
        factory.connect("setup", on_setup)

        self.files.set_factory(factory)

    def load_selected_folder(self, folder: Gio.File):
        children = Gtk.DirectoryList.new("standard::display-name", folder)
        selection_model = Gtk.SingleSelection.new(children)

        def on_selected_file(selection, *_):
            selected_item = selection.get_selected_item()
            selected_file = selected_item.get_attribute_object("standard::file")
            guessed_language = self.language_manager.guess_language(selected_file.get_path(), None)
            self.buffer.set_language(guessed_language)
            source_file = GtkSource.File(location=selected_file)
            loader = GtkSource.FileLoader.new(self.buffer, source_file)
            loader.load_async(GLib.PRIORITY_DEFAULT, None, None, None, None, None)

        selection_model.connect("selection_changed", on_selected_file)
        self.files.set_model(selection_model)
        self.stack.set_visible_child_name("editor")

    def on_open_folder_action(self, *_):
        """Callback for the win.open-folder action."""

        def on_selected(dialog, result):
            try:
                folder = dialog.select_folder_finish(result)
                self.load_selected_folder(folder)
            except GLib.GError:
                print("Nothing selected")

        directory = Gio.File.new_for_path("/")
        dialog = Gtk.FileDialog(initial_folder=directory)
        dialog.select_folder(self, None, on_selected)

    def create_action(self, name, callback):
        """Add a window action

        Args:
            name: the name of the action
            callback: called when the action is activated
        """
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
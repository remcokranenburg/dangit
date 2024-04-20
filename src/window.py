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

from gi.repository import Adw, Gio, Gtk, GtkSource, GLib, Pango

from dangit.files import FilesListFactory, FilesTreeListModel


class ProjectsListFactory(Gtk.SignalListItemFactory):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.connect("bind", self.bind)
        self.connect("setup", self.setup)

    @staticmethod
    def bind(self, list_item):
        box: Gtk.Box = list_item.get_child()
        title_label = box.get_first_child().get_first_child()
        subtitle_label = box.get_first_child().get_last_child()
        model: Gio.File = list_item.get_item()
        fileinfo = model.query_info("standard::display-name", Gio.FileQueryInfoFlags.NONE)
        title_label.set_label(fileinfo.get_display_name())
        subtitle_label.set_label(model.get_uri())

    @staticmethod
    def setup(self, list_item):
        box = Gtk.Box(
            margin_top=12,
            margin_bottom=12,
            margin_start=12,
            margin_end=12,
            orientation=Gtk.Orientation.HORIZONTAL,
        )
        title_box = Gtk.Box(
            margin_start=6, hexpand=True, orientation=Gtk.Orientation.VERTICAL, spacing=6
        )
        title_attributes = Pango.AttrList.new()
        title_attributes.insert(Pango.attr_weight_new(Pango.Weight.BOLD))
        title_label = Gtk.Label(
            xalign=0.0,
            max_width_chars=0,
            attributes=title_attributes,
            name="title",
        )
        subtitle_label = Gtk.Label(
            xalign=0.0,
            max_width_chars=0,
            css_classes=["dim-label"],
            name="subtitle",
        )
        title_box.append(title_label)
        title_box.append(subtitle_label)
        box.append(title_box)

        next_image = Gtk.Image(icon_name="go-next-symbolic", margin_start=12)
        box.append(next_image)

        list_item.set_child(box)


@Gtk.Template(resource_path="/com/remcokranenburg/Dangit/window.ui")
class DangitWindow(Adw.ApplicationWindow):
    __gtype_name__ = "DangitWindow"

    # ui elements
    projects_view: Gtk.ListView = Gtk.Template.Child()
    stack: Gtk.Stack = Gtk.Template.Child()
    editor: GtkSource.View = Gtk.Template.Child()
    files: Gtk.ListView = Gtk.Template.Child()

    # os
    os_settings: Gtk.Settings

    # project data
    recent_manager: Gtk.RecentManager
    projects: Gio.ListStore
    buffer: GtkSource.Buffer

    # theming
    language_manager: GtkSource.LanguageManager
    style_scheme_manager: GtkSource.StyleSchemeManager

    def update_recent_projects(self, recent_manager):
        self.projects.remove_all()
        recent_items = recent_manager.get_items()

        for item in recent_items:
            exists = item.exists()

            if exists:
                self.projects.append(Gio.File.new_for_uri(item.get_uri()))

    def __init__(self, recent_manager, projects, **kwargs):
        super().__init__(**kwargs)

        self.recent_manager = recent_manager
        self.projects = projects
        self.buffer = self.editor.get_buffer()
        self.language_manager = GtkSource.LanguageManager.get_default()
        self.style_scheme_manager = GtkSource.StyleSchemeManager.get_default()

        self.create_action("open-folder", self.on_open_folder_action)

        self.editor.set_smart_backspace(True)
        self.editor.set_show_line_marks(True)

        app_settings = Gio.Settings.new("com.remcokranenburg.Dangit")

        # set initial values
        self.set_property("maximized", app_settings.get_boolean("window-maximized"))
        self.set_property("default-width", app_settings.get_int("window-width"))
        self.set_property("default-height", app_settings.get_int("window-height"))

        # update settings when window is resized
        app_settings.bind("window-maximized", self, "maximized", Gio.SettingsBindFlags.SET)
        app_settings.bind("window-width", self, "default-width", Gio.SettingsBindFlags.SET)
        app_settings.bind("window-height", self, "default-height", Gio.SettingsBindFlags.SET)

        self.os_settings = Gtk.Settings.get_default()
        self.os_settings.connect("notify::gtk-application-prefer-dark-theme", self.set_editor_style)
        self.set_editor_style()

        provider = Gtk.CssProvider()
        provider.load_from_data("textview { font-family: Monospace; }")
        style_context = self.editor.get_style_context()
        style_context.add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self.files.set_factory(FilesListFactory())

        self.update_recent_projects(self.recent_manager)
        self.recent_manager.connect("changed", self.update_recent_projects)
        self.projects_view.set_factory(ProjectsListFactory())

        def on_selected_project(selection, *_):
            selected_folder = selection.get_selected_item()
            self.load_selected_folder(selected_folder)

        selection_model = Gtk.SingleSelection(autoselect=False, model=self.projects)
        selection_model.connect("selection_changed", on_selected_project)
        self.projects_view.set_model(selection_model)

    def set_editor_style(self, *_):
        if self.os_settings.get_property("gtk-application-prefer-dark-theme"):
            self.buffer.set_style_scheme(self.style_scheme_manager.get_scheme("classic-dark"))
        else:
            self.buffer.set_style_scheme(self.style_scheme_manager.get_scheme("classic"))

    def load_selected_folder(self, folder: Gio.File):
        files_tree_model = FilesTreeListModel(folder)
        selection_model = Gtk.SingleSelection.new(files_tree_model)

        def on_selected_file(selection, *_):
            selected_row = selection.get_selected_item()
            selected_file = selected_row.get_item().get_attribute_object("standard::file")
            guessed_language = self.language_manager.guess_language(selected_file.get_path(), None)
            self.buffer = GtkSource.Buffer()
            self.set_editor_style()
            self.buffer.set_language(guessed_language)
            self.editor.set_buffer(self.buffer)
            source_file = GtkSource.File(location=selected_file)
            loader = GtkSource.FileLoader.new(self.buffer, source_file)
            loader.load_async(GLib.PRIORITY_DEFAULT, None, None, None, None, None)

            def save_buffer(buffer):
                """Save the buffer to the file"""
                source_file = GtkSource.File(location=selected_file)
                if source_file:
                    saver = GtkSource.FileSaver.new(buffer, source_file)
                    saver.save_async(GLib.PRIORITY_DEFAULT, None, None, None, None, None)

            self.buffer.connect("changed", save_buffer)

        selection_model.connect("selection_changed", on_selected_file)
        self.files.set_model(selection_model)
        self.stack.set_visible_child_name("editor")

    def on_open_folder_action(self, *_):
        """Callback for the win.open-folder action."""

        def on_selected(dialog, result):
            try:
                folder = dialog.select_folder_finish(result)
                self.recent_manager.add_item(folder.get_uri())
                self.load_selected_folder(folder)
            except GLib.GError:
                print("Nothing selected")

        directory = Gio.File.new_for_path(GLib.get_home_dir())
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

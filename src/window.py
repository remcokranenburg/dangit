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

from gi.repository import Adw
from gi.repository import Gtk
from gi.repository import GtkSource
from gi.repository import GLib

@Gtk.Template(resource_path='/com/remcokranenburg/Dangit/window.ui')
class DangitWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'DangitWindow'

    stack = Gtk.Template.Child()
    editor = Gtk.Template.Child()
    files = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.editor.set_smart_backspace(True)
        self.editor.set_show_line_marks(True)

        provider = Gtk.CssProvider()
        provider.load_from_data("textview { font-family: Monospace; }")
        self.editor.get_style_context().add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

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

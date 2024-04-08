from gi.repository import Gtk, Gio


class FilesListFactory(Gtk.SignalListItemFactory):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.connect("bind", self.bind)
        self.connect("setup", self.setup)

    @staticmethod
    def bind(_self, list_item: Gtk.ListItem):
        row = list_item.get_item()
        expander = list_item.get_child()
        expander.set_list_row(row)
        model = row.get_item()
        box = expander.get_child()
        label = box.get_last_child()
        label.set_label(model.get_display_name())

    @staticmethod
    def setup(_self, list_item: Gtk.ListItem):
        box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
        box.append(Gtk.Label.new())
        expander = Gtk.TreeExpander()
        expander.set_child(box)
        list_item.set_child(expander)


def create_files_tree_list_model(directory: Gio.File):
    def create_func(item: Gio.FileInfo):
        if item.get_file_type() == Gio.FileType.DIRECTORY:
            file = item.get_attribute_object("standard::file")
            return Gtk.DirectoryList.new("standard::display-name,standard::type", file=file)
        else:
            return None

    root = Gtk.DirectoryList.new("standard::display-name,standard::type", file=directory)
    return Gtk.TreeListModel.new(root, False, False, create_func)

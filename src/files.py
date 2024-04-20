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


def create_filtered_directory_list(directory: Gio.File):
    file_attributes = ",".join(
        [
            "standard::display-name",
            "standard::type",
            "standard::is-hidden",
        ]
    )
    filter = Gtk.CustomFilter.new(lambda f: not f.get_is_hidden())
    root = Gtk.DirectoryList.new(file_attributes, file=directory)
    return Gtk.FilterListModel.new(root, filter)


def create_files_tree_list_model(directory: Gio.File):
    def create_func(item: Gio.FileInfo):
        if item.get_file_type() == Gio.FileType.DIRECTORY:
            file = item.get_attribute_object("standard::file")
            return create_filtered_directory_list(file)
        else:
            return None

    def sort_func(a: Gio.FileInfo, b: Gio.FileInfo, _user_data=None):
        a_name = a.get_display_name()
        b_name = b.get_display_name()
        a_is_directory = a.get_file_type() == Gio.FileType.DIRECTORY
        b_is_directory = b.get_file_type() == Gio.FileType.DIRECTORY

        if a_is_directory and not b_is_directory:
            return -1
        elif not a_is_directory and b_is_directory:
            return 1
        elif a_name == b_name:
            return 0
        elif a_name < b_name:
            return -1
        else:
            return 1

    root = create_filtered_directory_list(directory)
    tree_list = Gtk.TreeListModel.new(root, False, False, create_func)
    sorter = Gtk.CustomSorter.new(sort_func)
    row_sorter = Gtk.TreeListRowSorter.new(sorter)
    return Gtk.SortListModel.new(tree_list, row_sorter)

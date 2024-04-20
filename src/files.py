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


class FilesTreeListModel(Gtk.SortListModel):
    app_settings: Gio.Settings
    root: Gtk.FilterListModel

    def __init__(self, directory: Gio.File):
        self.app_settings = Gio.Settings.new("com.remcokranenburg.Dangit")
        self.root = self.create_filtered_directory_list(directory)
        tree_list = Gtk.TreeListModel.new(self.root, False, False, self.create_func)
        sorter = Gtk.CustomSorter.new(self.sort_func)
        row_sorter = Gtk.TreeListRowSorter.new(sorter)
        super().__init__(model=tree_list, sorter=row_sorter)

        self.app_settings.connect("changed::show-hidden-files", self.on_show_hidden_files_changed)

    def create_func(self, item: Gio.FileInfo):
        if item.get_file_type() == Gio.FileType.DIRECTORY:
            file = item.get_attribute_object("standard::file")
            return self.create_filtered_directory_list(file)
        else:
            return None

    @staticmethod
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

    def filter_func(self, item: Gio.FileInfo):
        if self.app_settings.get_boolean("show-hidden-files"):
            return True
        else:
            return not item.get_is_hidden()

    def create_filtered_directory_list(self, directory: Gio.File):
        file_attributes = ",".join(
            [
                "standard::display-name",
                "standard::type",
                "standard::is-hidden",
            ]
        )
        filter = Gtk.CustomFilter.new(self.filter_func)
        root = Gtk.DirectoryList.new(file_attributes, file=directory)
        return Gtk.FilterListModel.new(root, filter)

    def on_show_hidden_files_changed(self, _settings, _key):
        self.root.set_filter(Gtk.CustomFilter.new(self.filter_func))

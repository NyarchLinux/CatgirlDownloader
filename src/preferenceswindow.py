import os
from gi.repository import Gtk, Gio, Adw
from .preferences import UserPreferences
from .types import NSFWOption

@Gtk.Template(resource_path='/moe/nyarchlinux/catgirldownloader/../data/ui/preferences.ui')
class PreferencesWindow(Adw.PreferencesWindow):
    __gtype_name__ = 'PreferencesWindow'

    nsfw_dropdown = Gtk.Template.Child("nsfw_dropdown")
    auto_reload_seconds = Gtk.Template.Child("auto_reload_seconds")
    download_path_row = Gtk.Template.Child("download_path_row")
    download_path_button = Gtk.Template.Child("download_path_button")
    auto_save_switch = Gtk.Template.Child("auto_save_switch")

    def __init__(self, window, **kwargs):
        super().__init__(**kwargs)
        self.window = window
        self.settings = UserPreferences()

        self._nsfw_options = [option.value for option in NSFWOption]

        model = Gtk.StringList.new(self._nsfw_options)
        self.nsfw_dropdown.set_model(model)

        current = self.settings.get_preference("nsfw_mode") or NSFWOption.BLOCK_NSFW
        try:
            index = self._nsfw_options.index(current)
        except ValueError:
            index = 0
        self.nsfw_dropdown.set_selected(index)

        self.nsfw_dropdown.connect("notify::selected", self.on_nsfw_change)

        seconds = self.settings.get_preference("auto_reload_interval")
        try:
            seconds = int(seconds) if seconds is not None else 30
        except Exception:
            seconds = 30
        if seconds < 1:
            seconds = 1
        self.auto_reload_seconds.set_value(seconds)
        self.auto_reload_seconds.connect("value-changed", self.on_auto_reload_seconds_change)

        self.update_download_path_row()
        self.download_path_button.connect("clicked", self.on_choose_download_path)

        self.auto_save_switch.set_active(self.settings.get_auto_save_enabled())
        self.auto_save_switch.connect("notify::active", self.on_auto_save_toggle)

    def update_download_path_row(self):
        path = self.settings.get_download_path()
        self.download_path_row.set_subtitle(path)
        self.download_path_button.set_label(os.path.basename(path) or path)

    def on_choose_download_path(self, button):
        dialog = Gtk.FileChooserDialog(title="Select download folder", parent=self,
                                       action=Gtk.FileChooserAction.SELECT_FOLDER)
        dialog.add_button('Cancel', Gtk.ResponseType.CANCEL)
        dialog.add_button('Select', Gtk.ResponseType.OK)
        dialog.set_current_folder(Gio.File.new_for_path(self.settings.get_download_path()))
        dialog.connect('response', self.on_download_path_response)
        dialog.show()

    def on_download_path_response(self, dialog, response_id):
        if response_id == Gtk.ResponseType.OK:
            file = dialog.get_file()
            if file is not None:
                self.settings.set_preference("download_path", file.get_path())
                self.update_download_path_row()
        dialog.destroy()

    def on_auto_save_toggle(self, switch, _):
        self.settings.set_preference("auto_save_enabled", bool(switch.get_active()))

    def on_nsfw_change(self, dropdown, _):
        index = dropdown.get_selected()
        if index is None or index < 0 or index >= len(self._nsfw_options):
            return
        value = self._nsfw_options[index]
        self.settings.set_preference("nsfw_mode", value)

    def on_auto_reload_seconds_change(self, spin):
        seconds = int(spin.get_value())
        if seconds < 1:
            seconds = 1
        self.settings.set_preference("auto_reload_interval", seconds)
        if self.window is not None and hasattr(self.window, "set_auto_reload_interval"):
            self.window.set_auto_reload_interval(seconds)


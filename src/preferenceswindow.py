from gi.repository import Gtk, Adw
from .preferences import UserPreferences
from .types import NSFWOption

@Gtk.Template(resource_path='/moe/nyarchlinux/catgirldownloader/../data/ui/preferences.ui')
class PreferencesWindow(Adw.PreferencesWindow):
    __gtype_name__ = 'PreferencesWindow'

    nsfw_dropdown = Gtk.Template.Child("nsfw_dropdown")
    auto_reload_seconds = Gtk.Template.Child("auto_reload_seconds")

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


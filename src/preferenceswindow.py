from gi.repository import GLib, Gtk, Adw
from .preferences import UserPreferences

@Gtk.Template(resource_path='/moe/furry/catgirldownloader/../data/ui/preferences.ui')
class PreferencesWindow(Adw.PreferencesWindow):
    __gtype_name__ = 'PreferencesWindow'
    nsfw_switch = Gtk.Template.Child("nsfw")

    def __init__(self, window, **kwargs):
        super().__init__(**kwargs)
        self.window = window
        self.settings = UserPreferences()
        print(self.settings.get_preference("nsfw"))
        self.nsfw_switch.set_state(self.settings.get_preference("nsfw"))
        self.nsfw_switch.connect('notify::active', self.toggle_nsfw)

    def toggle_nsfw(self, switch, _active):
        pref = self.nsfw_switch.get_active()
        self.settings.set_preference("nsfw", pref)

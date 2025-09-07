from gi.repository import GLib, Gtk, Adw
from .preferences import UserPreferences

@Gtk.Template(resource_path='/moe/furry/catgirldownloader/../data/ui/preferences.ui')
class PreferencesWindow(Adw.PreferencesWindow):
    __gtype_name__ = 'PreferencesWindow'
    nsfw_switch = Gtk.Template.Child("nsfw")
    source_selector = Gtk.Template.Child("source")
    e621_tags_entry = Gtk.Template.Child("e621_tags")

    def __init__(self, window, **kwargs):
        super().__init__(**kwargs)
        self.window = window
        self.settings = UserPreferences()
        self.nsfw_switch.set_state(self.settings.get_preference("nsfw"))
        self.nsfw_switch.connect('notify::active', self.toggle_nsfw)

        # Initialize source selector
        # Only furry source (e621)
        self.source_selector.append_text('e621')
        self.source_selector.set_active(0)
        self.source_selector.connect('changed', self.change_source)

        # Initialize e621 tags entry
        self.e621_tags_entry.set_text(self.settings.get_preference("e621_tags") or "")
        self.e621_tags_entry.connect('changed', self.change_e621_tags)

    def toggle_nsfw(self, switch, _active):
        pref = self.nsfw_switch.get_active()
        self.settings.set_preference("nsfw", pref)

    def change_source(self, combo):
        text = combo.get_active_text()
        if text:
            self.settings.set_preference("source", text)

    def change_e621_tags(self, entry):
        self.settings.set_preference("e621_tags", entry.get_text())

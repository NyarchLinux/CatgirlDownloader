from gi.repository import GLib, Gtk, Adw
from .preferences import UserPreferences

@Gtk.Template(resource_path='/moe/Avelcius/furrydownloader/../data/ui/preferences.ui')
class PreferencesWindow(Adw.PreferencesWindow):
    __gtype_name__ = 'PreferencesWindow'
    rating_selector = Gtk.Template.Child("rating")
    source_selector = Gtk.Template.Child("source")
    e621_tags_entry = Gtk.Template.Child("e621_tags")

    def __init__(self, window, **kwargs):
        super().__init__(**kwargs)
        self.window = window
        self.settings = UserPreferences()
        # Rating selector
        for r in ['explicit', 'questionable', 'safe']:
            self.rating_selector.append_text(r)
        current_rating = self.settings.get_preference("rating") or 'safe'
        try:
            idx = ['explicit', 'questionable', 'safe'].index(current_rating)
        except Exception:
            idx = 2
        self.rating_selector.set_active(idx)
        self.rating_selector.connect('changed', self.change_rating)

        # Initialize source selector
        # Only furry source (e621)
        self.source_selector.append_text('e621')
        self.source_selector.set_active(0)
        self.source_selector.connect('changed', self.change_source)

        # Initialize e621 tags entry
        self.e621_tags_entry.set_text(self.settings.get_preference("e621_tags") or "")
        self.e621_tags_entry.connect('changed', self.change_e621_tags)

    def change_rating(self, combo):
        text = combo.get_active_text()
        if text:
            self.settings.set_preference("rating", text)

    def change_source(self, combo):
        text = combo.get_active_text()
        if text:
            self.settings.set_preference("source", text)

    def change_e621_tags(self, entry):
        self.settings.set_preference("e621_tags", entry.get_text())

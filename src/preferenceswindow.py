from gi.repository import Gtk, Adw
from .preferences import UserPreferences
from .types import NSFWOption


def show_conflict_warning(parent, conflicting_tags):
    if not conflicting_tags:
        return

    dialog = Adw.MessageDialog(modal=True, heading="Tag Conflict Detected")
    dialog.set_body_use_markup(True)
    dialog.set_body(
        f"The following tags are in both Search and Blacklist:\n"
        f"<b>{', '.join(conflicting_tags)}</b>\n\n"
        f"This will result in no images being found. Please remove these tags from either Search or Blacklist."
    )

    toplevel = parent
    while toplevel and not isinstance(toplevel, Gtk.Window):
        toplevel = (
            toplevel.get_ancestor(Gtk.Window)
            if hasattr(toplevel, "get_ancestor")
            else None
        )
        if toplevel:
            break

    if toplevel:
        dialog.set_transient_for(toplevel)

    dialog.add_response("ok", "OK")
    dialog.present()


def check_all_sources_for_conflict(settings):
    from .danbooru import DanbooruDownloaderAPI

    settings.reload_preferences()

    all_conflicts = []

    danbooru = DanbooruDownloaderAPI(settings=settings)
    danbooru.reload_settings()
    conflicts = danbooru.check_search_blacklist_conflict()
    if conflicts:
        all_conflicts.extend([f"Danbooru: {', '.join(conflicts)}"])

    return all_conflicts


@Gtk.Template(
    resource_path="/moe/nyarchlinux/catgirldownloader/../data/ui/preferences.ui"
)
class PreferencesWindow(Adw.PreferencesWindow):
    __gtype_name__ = "PreferencesWindow"

    nsfw_dropdown = Gtk.Template.Child("nsfw_dropdown")
    auto_reload_seconds = Gtk.Template.Child("auto_reload_seconds")
    blacklist_tags_entry = Gtk.Template.Child("blacklist_tags_entry")

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
        self.auto_reload_seconds.connect(
            "value-changed", self.on_auto_reload_seconds_change
        )

        blacklist_tags = self.settings.get_preference("blacklist_tags") or ""
        self.blacklist_tags_entry.set_text(blacklist_tags)
        self.blacklist_tags_entry.connect("changed", self.on_blacklist_tags_change)

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

    def on_blacklist_tags_change(self, entry):
        tags = entry.get_text()
        self.settings.set_preference("blacklist_tags", tags)

        conflicts = check_all_sources_for_conflict(self.settings)
        if conflicts:
            show_conflict_warning(
                self, [c.split(": ", 1)[1] for c in conflicts if ": " in c]
            )

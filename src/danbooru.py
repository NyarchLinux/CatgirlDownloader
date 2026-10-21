import requests
import json
import time
import base64
import threading
from typing import Optional, Any

from .types import NSFWOption
from .api_base import BaseDownloaderAPI

# TODO: Surely, there must be a better way to encode these. I don't think listing the tags explicitly would be a good idea. --PCBoy
_FORBIDDEN_TAG_1 = base64.b64decode('c2hvdGE='.encode('utf-8')).decode('utf-8')
_FORBIDDEN_TAG_2 = base64.b64decode('bG9saQ=='.encode('utf-8')).decode('utf-8')
_REQUEST_HEADERS = {
    "User-Agent": "CatgirlDownloader/1.0 (+https://github.com/NyarchLinux/CatgirlDownloader)"
}
_BATCH_SIZE = 20
_MAX_ANONYMOUS_TAGS = 2
_SUGGESTION_DELAY_MS = 300
_SUGGESTION_LIMIT = 10
_FALLBACK_EXTENSIONS = {"jpg", "jpeg", "png", "gif"}


def _displayable_extensions() -> set[str]:
    """File extensions the installed GdkPixbuf loaders can decode
    (webp/avif only when the matching loader package is installed)."""
    try:
        from gi.repository import GdkPixbuf
        exts = {ext.lower()
                for fmt in GdkPixbuf.Pixbuf.get_formats()
                for ext in fmt.get_extensions()}
        return exts or set(_FALLBACK_EXTENSIONS)
    except Exception:
        return set(_FALLBACK_EXTENSIONS)


def _is_forbidden_tag(name: str) -> bool:
    words = name.lower().split("_")
    return _FORBIDDEN_TAG_1 in words or _FORBIDDEN_TAG_2 in words


def _fetch_tag_suggestions(word: str) -> list[tuple[str, int]]:
    """Most used Danbooru tags starting with 'word', as (name, post count)."""
    try:
        r = requests.get(
            "https://danbooru.donmai.us/tags.json",
            params={
                "search[name_matches]": f"{word}*",
                "search[order]": "count",
                "limit": _SUGGESTION_LIMIT,
            },
            headers=_REQUEST_HEADERS,
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"Tag autocomplete failed: {e}")
        return []
    if not isinstance(data, list):
        return []
    return [(tag["name"], tag.get("post_count", 0))
            for tag in data
            if isinstance(tag, dict) and tag.get("name")
            and not _is_forbidden_tag(tag["name"])]


class _TagAutocomplete:
    """Suggests existing Danbooru tags for the word under the cursor of an entry."""

    def __init__(self, entry: Any, listbox: Any, revealer: Any) -> None:
        self._entry = entry
        self._listbox = listbox
        self._revealer = revealer
        self._timeout_id = 0
        self._generation = 0
        self._suppress = False
        entry.connect("changed", self._on_changed)
        listbox.connect("row-activated", self._on_row_activated)

    def _current_word(self) -> tuple[int, int]:
        """Start and end offsets of the word under the cursor."""
        text = self._entry.get_text()
        pos = self._entry.get_position()
        start = text.rfind(" ", 0, pos) + 1
        end = text.find(" ", pos)
        return start, len(text) if end == -1 else end

    def _on_changed(self, _entry: Any) -> None:
        from gi.repository import GLib

        self._generation += 1
        if self._timeout_id:
            GLib.source_remove(self._timeout_id)
            self._timeout_id = 0
        if self._suppress:
            self._hide()
            return
        # Wait until the user stops typing before querying Danbooru.
        self._timeout_id = GLib.timeout_add(_SUGGESTION_DELAY_MS, self._on_timeout)

    def _on_timeout(self) -> bool:
        self._timeout_id = 0
        start, end = self._current_word()
        word = self._entry.get_text()[start:end].lower().lstrip("-")
        if not word or _is_forbidden_tag(word):
            self._hide()
            return False
        generation = self._generation
        threading.Thread(target=self._fetch_thread, args=(word, generation), daemon=True).start()
        return False

    def _fetch_thread(self, word: str, generation: int) -> None:
        from gi.repository import GLib

        suggestions = _fetch_tag_suggestions(word)
        GLib.idle_add(self._show, suggestions, generation)

    def _show(self, suggestions: list[tuple[str, int]], generation: int) -> bool:
        from gi.repository import Gtk, Pango

        # Drop answers for text the user has already changed.
        if generation != self._generation:
            return False
        self._listbox.remove_all()
        for name, count in suggestions:
            box = Gtk.Box(spacing=12)
            box.set_margin_top(6)
            box.set_margin_bottom(6)
            box.set_margin_start(12)
            box.set_margin_end(12)
            name_label = Gtk.Label(label=name, xalign=0)
            name_label.set_hexpand(True)
            name_label.set_ellipsize(Pango.EllipsizeMode.END)
            box.append(name_label)
            count_label = Gtk.Label(label=f"{count:,} images".replace(",", "\u202f"))
            count_label.add_css_class("dim-label")
            count_label.add_css_class("caption")
            box.append(count_label)
            row = Gtk.ListBoxRow()
            row.set_child(box)
            row.tag_name = name
            self._listbox.append(row)
        self._revealer.set_reveal_child(bool(suggestions))
        return False

    def _hide(self) -> None:
        self._revealer.set_reveal_child(False)

    def _on_row_activated(self, _listbox: Any, row: Any) -> None:
        text = self._entry.get_text()
        start, end = self._current_word()
        prefix = "-" if text[start:end].startswith("-") else ""
        new_text = text[:start] + prefix + row.tag_name + " " + text[end:].lstrip(" ")
        self._suppress = True
        self._entry.set_text(new_text)
        self._suppress = False
        self._entry.grab_focus()
        self._entry.set_position(start + len(prefix) + len(row.tag_name) + 1)
        self._hide()


class DanbooruDownloaderAPI(BaseDownloaderAPI):
    def __init__(self, settings=None) -> None:
        super().__init__()
        self.endpoint = "https://danbooru.donmai.us"
        self._settings = settings
        self._load_tags()
        self._settings_window = None

    def _load_tags(self) -> None:
        if self._settings:
            self.tags = self._settings.get_preference("danbooru_tags") or ""
        else:
            self.tags = ""

    def set_tags(self, tags: str) -> None:
        self.tags = tags

    def get_tags(self) -> str:
        return self.tags

    def get_request_headers(self) -> dict[str, str]:
        return dict(_REQUEST_HEADERS)

    def _build_tags_query(self, nsfw_mode: NSFWOption) -> str:
        tags = self.tags.strip() if self.tags else ""

        if nsfw_mode == NSFWOption.BLOCK_NSFW or nsfw_mode == NSFWOption.BLOCK_NSFW.value:
            rating_tag = "rating:general"
        elif nsfw_mode == NSFWOption.ONLY_NSFW or nsfw_mode == NSFWOption.ONLY_NSFW.value:
            rating_tag = "rating:explicit"
        else:
            rating_tag = None

        if tags and rating_tag:
            return f"{tags} {rating_tag}"
        elif rating_tag:
            return rating_tag
        return tags

    @staticmethod
    def _error_from_response(r: requests.Response) -> str:
        # Danbooru explains refused searches in JSON, e.g. the 2-tag limit
        # for anonymous users ("You cannot search for more than 2 tags...").
        try:
            message = r.json().get("message")
            if message:
                return f"Danbooru: {message}"
        except Exception:
            pass
        return f"Danbooru answered with HTTP {r.status_code}"

    def get_random_post(self, nsfw_mode: NSFWOption = NSFWOption.BLOCK_NSFW, max_retries: int = 3) -> Optional[dict]:
        self.last_error = None
        tags = self._build_tags_query(nsfw_mode)
        # Ask for a batch of random posts and keep the first usable one:
        # many posts are videos/ugoira (not loadable by GdkPixbuf) or have
        # no file_url for anonymous users, and a single random post would
        # then leave the window unchanged.
        params = {
            "limit": _BATCH_SIZE,
            "random": "true"
        }
        if tags:
            params["tags"] = tags
        displayable = _displayable_extensions()

        for attempt in range(max_retries):
            try:
                r = requests.get(
                    f"{self.endpoint}/posts.json",
                    params=params,
                    headers=_REQUEST_HEADERS,
                    timeout=10,
                )
            except Exception as e:
                print(e)
                self.last_error = "Could not reach Danbooru"
                return None
            if r.status_code != 200:
                self.last_error = self._error_from_response(r)
                print(self.last_error)
                return None
            try:
                data = r.json()
            except ValueError:
                self.last_error = "Danbooru sent an invalid response"
                return None
            if not isinstance(data, list) or not data:
                self.last_error = "No Danbooru posts match these tags"
                return None

            for post in data:
                post_tags = post.get('tag_string', '').split()
                if _FORBIDDEN_TAG_1 in post_tags or _FORBIDDEN_TAG_2 in post_tags:
                    continue
                if not post.get("file_url"):
                    continue
                if (post.get("file_ext") or "").lower() not in displayable:
                    continue
                self.info = post
                return post
            print(f'Attempt {attempt + 1}: no displayable post in batch, retrying...')

        print(f'Could not find suitable post after {max_retries} attempts')
        self.last_error = "No displayable Danbooru image found for these tags"
        return None

    def get_image_url(self, nsfw_mode: NSFWOption = NSFWOption.BLOCK_NSFW) -> Optional[str]:
        post = self.get_random_post(nsfw_mode)
        if post:
            return post.get("file_url")
        return None

    def get_artist(self, info: Optional[dict] = None) -> Optional[str]:
        data = info if info else self.info
        if not data:
            return None
        try:
            artist_tags = data.get("tag_string_artist", "")
            if artist_tags:
                return artist_tags.split(" ")[0]
            return None
        except Exception:
            return None

    def get_link(self, info: Optional[dict] = None) -> Optional[str]:
        data = info if info else self.info
        if not data:
            return None
        try:
            post_id = data.get("id")
            if post_id:
                return f"{self.endpoint}/posts/{post_id}"
            return None
        except Exception:
            return None

    def get_filename_suggestion(self, extension: Optional[str], info: Optional[dict] = None) -> str:
        data = info if info else self.info
        if not data:
            post_id = str(int(time.time()))
        else:
            try:
                post_id = str(data.get("id", int(time.time())))
            except Exception:
                post_id = str(int(time.time()))

        if extension:
            return f"danbooru_{post_id}.{extension}"
        return f"danbooru_{post_id}"

    def open_settings_window(self, parent: Any) -> None:
        from gi.repository import Gtk, Adw

        window = Adw.PreferencesWindow()
        window.set_title("Danbooru Settings")
        window.set_modal(True)

        if isinstance(parent, Gtk.Window):
            window.set_transient_for(parent)
        else:
            toplevel = parent.get_ancestor(Gtk.Window)
            if toplevel:
                window.set_transient_for(toplevel)

        page = Adw.PreferencesPage()
        window.add(page)

        group = Adw.PreferencesGroup()
        group.set_title("Tags")
        page.add(group)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_margin_top(12)
        vbox.set_margin_bottom(12)
        vbox.set_margin_start(12)
        vbox.set_margin_end(12)

        title_label = Gtk.Label(label="Search Tags")
        title_label.add_css_class("heading")
        title_label.set_halign(Gtk.Align.START)
        vbox.append(title_label)

        desc_label = Gtk.Label(
            label="Separate tags with spaces and write multi-word tags with "
                  "underscores (cat_ears, not \"cat ears\"). Put a minus "
                  "before a tag to exclude it (-cat_ears). Without a Danbooru "
                  f"account you can use at most {_MAX_ANONYMOUS_TAGS} tags."
        )
        desc_label.add_css_class("caption")
        desc_label.set_halign(Gtk.Align.START)
        desc_label.set_xalign(0)
        desc_label.set_wrap(True)
        vbox.append(desc_label)

        entry = Gtk.Entry()
        entry.set_text(self.tags)
        entry.set_placeholder_text("e.g., cat_ears solo")
        entry.set_hexpand(True)
        entry.connect("changed", lambda e: self._on_tags_changed(e, window))
        vbox.append(entry)

        count_label = Gtk.Label()
        count_label.add_css_class("caption")
        count_label.set_halign(Gtk.Align.END)
        vbox.append(count_label)
        entry.connect("changed", lambda e: self._update_tag_count(e, count_label))
        self._update_tag_count(entry, count_label)

        suggestions = Gtk.ListBox()
        suggestions.set_selection_mode(Gtk.SelectionMode.NONE)
        suggestions.add_css_class("boxed-list")
        revealer = Gtk.Revealer()
        revealer.set_child(suggestions)
        vbox.append(revealer)
        window._tag_autocomplete = _TagAutocomplete(entry, suggestions, revealer)

        row = Adw.PreferencesRow()
        row.set_child(vbox)
        group.add(row)

        window.connect("close-request", lambda e: self._on_prefs_close(entry, parent))

        self._settings_window = window
        window.present()

    def _on_tags_changed(self, entry: Any, window: Any) -> None:
        tagcheck = entry.get_text().lower().split()
        while _FORBIDDEN_TAG_1 in tagcheck:
            tagcheck.remove(_FORBIDDEN_TAG_1)
        while _FORBIDDEN_TAG_2 in tagcheck:
            tagcheck.remove(_FORBIDDEN_TAG_2)
        self.tags = ' '.join(tagcheck)
        if self._settings:
            self._settings.set_preference("danbooru_tags", self.tags)

    def _update_tag_count(self, entry: Any, label: Any) -> None:
        count = len(entry.get_text().split())
        label.set_label(f"{count}/{_MAX_ANONYMOUS_TAGS} tags")
        if count > _MAX_ANONYMOUS_TAGS:
            label.add_css_class("warning")
            entry.add_css_class("warning")
        else:
            label.remove_css_class("warning")
            entry.remove_css_class("warning")

    def _on_prefs_close(self, text: Any, parent: Any) -> None:
        tagcheck = text.get_text().lower().split()
        if _FORBIDDEN_TAG_1 in tagcheck or _FORBIDDEN_TAG_2 in tagcheck:
            self.open_forbid_tag_notif(parent)

    def open_forbid_tag_notif(self, parent: Any) -> None:
        from gi.repository import Gtk, Adw

        dialog = Adw.MessageDialog(
            modal = True,
            heading = "Danbooru Settings",
        )
        dialog.set_body_use_markup(True)
        dialog.set_body('Due to a limitation of Danbooru, certain tags have been automatically removed from your settings. For more information, please visit <a href="https://danbooru.donmai.us/wiki_pages/help:censored_tags">Danbooru\'s "censored tags" help page</a>.')

        if isinstance(parent, Gtk.Window):
            dialog.set_transient_for(parent)
        else:
            toplevel = parent.get_ancestor(Gtk.Window)
            if toplevel:
                dialog.set_transient_for(toplevel)

        dialog.add_response("ok", "OK")
        dialog.present()

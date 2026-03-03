import requests
import json
import time
from typing import Optional, Any

from .types import NSFWOption
from .api_base import BaseDownloaderAPI


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

    def set_tags(self, tags: str) -> None:
        self.tags = tags

    def get_tags(self) -> str:
        return self.tags

    def _build_tags_query(self, nsfw_mode: NSFWOption) -> str:
        tags = self.tags.strip() if self.tags else ""

        if nsfw_mode == NSFWOption.BLOCK_NSFW:
            rating_tag = "rating:safe"
        elif nsfw_mode == NSFWOption.ONLY_NSFW:
            rating_tag = "rating:explicit"
        else:
            rating_tag = None

        if tags and rating_tag:
            return f"{tags} {rating_tag}"
        elif rating_tag:
            return rating_tag
        return tags

    def get_random_post(self, nsfw_mode: NSFWOption = NSFWOption.BLOCK_NSFW) -> Optional[dict]:
        try:
            tags = self._build_tags_query(nsfw_mode)
            params = {
                "limit": 1,
                "random": "true"
            }
            if tags:
                params["tags"] = tags

            r = requests.get(f"{self.endpoint}/posts.json", params=params, timeout=10)
            if r.status_code != 200:
                return None
        except Exception as e:
            print(e)
            return None

        try:
            data = json.loads(r.text)
            if isinstance(data, list) and len(data) > 0:
                self.info = data[0]
                return data[0]
            return None
        except Exception:
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

        desc_label = Gtk.Label(label="Enter tags separated by spaces (e.g., cat_ears solo)")
        desc_label.add_css_class("caption")
        desc_label.set_halign(Gtk.Align.START)
        desc_label.set_wrap(True)
        vbox.append(desc_label)

        entry = Gtk.Entry()
        entry.set_text(self.tags)
        entry.set_placeholder_text("e.g., cat_ears solo 1girl")
        entry.set_hexpand(True)
        entry.connect("changed", lambda e: self._on_tags_changed(e, window))
        vbox.append(entry)

        row = Adw.PreferencesRow()
        row.set_child(vbox)
        group.add(row)

        self._settings_window = window
        window.present()

    def _on_tags_changed(self, entry: Any, window: Any) -> None:
        self.tags = entry.get_text()
        if self._settings:
            self._settings.set_preference("danbooru_tags", self.tags)

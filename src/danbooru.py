import requests
import json
import time
import base64
from typing import Optional, Any

from .types import NSFWOption
from .api_base import BaseDownloaderAPI

# TODO: Surely, there must be a better way to encode these. I don't think listing the tags explicitly would be a good idea. --PCBoy
_FORBIDDEN_TAG_1 = base64.b64decode("c2hvdGE=".encode("utf-8")).decode("utf-8")
_FORBIDDEN_TAG_2 = base64.b64decode("bG9saQ==".encode("utf-8")).decode("utf-8")


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
            self.blacklist_tags = self._settings.get_preference("blacklist_tags") or ""

    def set_tags(self, tags: str) -> None:
        self.tags = tags

    def get_tags(self) -> str:
        return self.tags

    def get_blacklist_tags(self) -> str:
        return self.blacklist_tags

    def reload_settings(self) -> None:
        self._load_tags()

    def check_search_blacklist_conflict(self) -> list:
        search_tags = set(self.tags.strip().lower().split()) if self.tags else set()
        blacklist_tags = set(self._parse_blacklist())
        return list(search_tags & blacklist_tags)

    def _build_tags_query(self, nsfw_mode: NSFWOption) -> str:
        tags = self.tags.strip() if self.tags else ""

        if (
            nsfw_mode == NSFWOption.BLOCK_NSFW
            or nsfw_mode == NSFWOption.BLOCK_NSFW.value
        ):
            rating_tag = "rating:general"
        elif (
            nsfw_mode == NSFWOption.ONLY_NSFW or nsfw_mode == NSFWOption.ONLY_NSFW.value
        ):
            rating_tag = "rating:explicit"
        else:
            rating_tag = None

        blacklist_parts = [f"-{tag}" for tag in self._parse_blacklist()]

        query_parts = []
        if tags:
            query_parts.append(tags)
        if rating_tag:
            query_parts.append(rating_tag)
        if blacklist_parts:
            query_parts.extend(blacklist_parts)

        return " ".join(query_parts)

    def get_random_post(
        self, nsfw_mode: NSFWOption = NSFWOption.BLOCK_NSFW, max_retries: int = 5
    ) -> Optional[dict]:
        for attempt in range(max_retries):
            try:
                tags = self._build_tags_query(nsfw_mode)
                params = {"limit": 1, "random": "true"}
                if tags:
                    params["tags"] = tags
                r = requests.get(
                    f"{self.endpoint}/posts.json", params=params, timeout=10
                )
                if r.status_code != 200:
                    return None
            except Exception as e:
                print(e)
                return None
            try:
                data = json.loads(r.text)
                if isinstance(data, list) and len(data) > 0:
                    post = data[0]
                    post_tags = post.get("tag_string", "").split()
                    if _FORBIDDEN_TAG_1 in post_tags or _FORBIDDEN_TAG_2 in post_tags:
                        print(
                            f"Attempt {attempt + 1}: Forbidden tags in post, retrying..."
                        )
                        continue

                    matched = self._check_blacklist_match(post_tags)
                    if matched:
                        print(
                            f"Attempt {attempt + 1}: Blacklisted tags found: {matched}, retrying..."
                        )
                        continue

                    self.info = post
                    return post
                return None
            except Exception:
                return None
        print(f"Could not find suitable post after {max_retries} attempts")
        return None

    def get_image_url(
        self, nsfw_mode: NSFWOption = NSFWOption.BLOCK_NSFW
    ) -> Optional[str]:
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

    def get_filename_suggestion(
        self, extension: Optional[str], info: Optional[dict] = None
    ) -> str:
        data = info if info else self.info
        post_id = self.get_filename_id(data)
        if extension:
            return f"danbooru_{post_id}.{extension}"
        return f"danbooru_{post_id}"

    def get_filename_id(self, info: dict = None) -> str:
        if info:
            return str(info.get("id", super().get_filename_id()))
        return super().get_filename_id()

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
            label="Enter tags separated by spaces (e.g., cat_ears solo)"
        )
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

        window.connect("close-request", lambda e: self._on_prefs_close(entry, parent))

        self._settings_window = window
        window.present()

    def _on_tags_changed(self, entry: Any, window: Any) -> None:
        tagcheck = entry.get_text().lower().split()
        while _FORBIDDEN_TAG_1 in tagcheck:
            tagcheck.remove(_FORBIDDEN_TAG_1)
        while _FORBIDDEN_TAG_2 in tagcheck:
            tagcheck.remove(_FORBIDDEN_TAG_2)
        self.tags = " ".join(tagcheck)
        if self._settings:
            self._settings.set_preference("danbooru_tags", self.tags)

    def _on_prefs_close(self, text: Any, parent: Any) -> None:
        tagcheck = text.get_text().lower().split()
        if _FORBIDDEN_TAG_1 in tagcheck or _FORBIDDEN_TAG_2 in tagcheck:
            self.open_forbid_tag_notif(parent)

    def open_forbid_tag_notif(self, parent: Any) -> None:
        from gi.repository import Gtk, Adw

        dialog = Adw.MessageDialog(
            modal=True,
            heading="Danbooru Settings",
        )
        dialog.set_body_use_markup(True)
        dialog.set_body(
            'Due to a limitation of Danbooru, certain tags have been automatically removed from your settings. For more information, please visit <a href="https://danbooru.donmai.us/wiki_pages/help:censored_tags">Danbooru\'s "censored tags" help page</a>.'
        )

        if isinstance(parent, Gtk.Window):
            dialog.set_transient_for(parent)
        else:
            toplevel = parent.get_ancestor(Gtk.Window)
            if toplevel:
                dialog.set_transient_for(toplevel)

        dialog.add_response("ok", "OK")
        dialog.present()

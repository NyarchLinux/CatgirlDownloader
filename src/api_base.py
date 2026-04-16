from abc import ABC, abstractmethod
from typing import Any, Optional, List
import requests
from .types import NSFWOption


class BaseDownloaderAPI(ABC):
    def __init__(self) -> None:
        self.endpoint: str = ""
        self.info: Optional[dict[str, Any]] = None
        self._settings = None
        self.blacklist_tags: str = ""

    @abstractmethod
    def get_image_url(
        self, nsfw_mode: NSFWOption = NSFWOption.BLOCK_NSFW
    ) -> Optional[str]:
        pass

    @abstractmethod
    def get_artist(self, info: Optional[dict] = None) -> Optional[str]:
        pass

    @abstractmethod
    def get_link(self, info: Optional[dict] = None) -> Optional[str]:
        pass

    def get_blacklist_tags(self) -> str:
        return self.blacklist_tags

    def _parse_blacklist(self) -> List[str]:
        if not self.blacklist_tags:
            return []
        return [tag for tag in self.blacklist_tags.strip().lower().split() if tag]

    def _check_blacklist_match(self, tags: List[str]) -> List[str]:
        blacklist = self._parse_blacklist()
        if not blacklist:
            return []
        tags_lower = [t.lower() for t in tags]
        return [tag for tag in blacklist if tag in tags_lower]

    def get_image(self, url: str) -> Optional[bytes]:
        try:
            r = requests.get(url, timeout=20)
            if r.status_code == 200:
                return r.content
            return None
        except Exception as e:
            print(f"Error downloading image: {e}")
            return None

    @abstractmethod
    def get_filename_suggestion(
        self, extension: Optional[str], info: Optional[dict] = None
    ) -> str:
        pass

    def get_filename_id(self, info: Optional[dict] = None) -> str:
        import time

        return str(int(time.time()))

    def open_settings_window(self, parent: Any) -> None:
        from gi.repository import Gio

        action = Gio.SimpleAction.new("preferences", None)
        action.activate(None)
        if hasattr(parent, "get_application"):
            app = parent.get_application()
            if app:
                app.activate_action("preferences", None)

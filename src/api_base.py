from abc import ABC, abstractmethod
from typing import Any, Optional
import requests
from .types import NSFWOption

class BaseDownloaderAPI(ABC):
    def __init__(self) -> None:
        self.endpoint: str = ""
        self.info: Optional[dict[str, Any]] = None
        # Human-readable reason for the last failed get_image_url() call,
        # shown to the user instead of failing silently.
        self.last_error: Optional[str] = None

    @abstractmethod
    def get_image_url(self, nsfw_mode: NSFWOption = NSFWOption.BLOCK_NSFW) -> Optional[str]:
        pass

    @abstractmethod
    def get_artist(self, info: Optional[dict] = None) -> Optional[str]:
        pass

    @abstractmethod
    def get_link(self, info: Optional[dict] = None) -> Optional[str]:
        pass

    def get_image(self, url: str) -> Optional[bytes]:
        try:
            r = requests.get(url, headers=self.get_request_headers(), timeout=20)
            # The original implementations didn't check status code explicitly in get_image
            # but usually relied on the caller or just returned content.
            # We'll return content if successful, or None on error for safety.
            if r.status_code == 200:
                return r.content
            return None
        except Exception as e:
            print(f"Error downloading image: {e}")
            return None

    def get_request_headers(self) -> dict[str, str]:
        """Return HTTP headers required by this image source."""
        return {}

    @abstractmethod
    def get_filename_suggestion(self, extension: Optional[str], info: Optional[dict] = None) -> str:
        pass

    def open_settings_window(self, parent: Any) -> None:
        """
        Opens a settings window for this downloader source.
        Override this method if the source has configurable settings.
        """
        # Default implementation opens the main application preferences.
        # 'parent' is usually the gear button inside the source dropdown, which
        # has no get_application(), so ask the running application directly.
        from gi.repository import Gio
        app = Gio.Application.get_default()
        if app is not None:
            app.activate_action("preferences", None)

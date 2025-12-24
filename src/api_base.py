from abc import ABC, abstractmethod
from typing import Any, Optional
import requests
from .types import NSFWOption

class BaseDownloaderAPI(ABC):
    def __init__(self) -> None:
        self.endpoint: str = ""
        self.info: Optional[dict[str, Any]] = None

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
            r = requests.get(url, timeout=20)
            # The original implementations didn't check status code explicitly in get_image
            # but usually relied on the caller or just returned content.
            # We'll return content if successful, or None on error for safety.
            if r.status_code == 200:
                return r.content
            return None
        except Exception as e:
            print(f"Error downloading image: {e}")
            return None

    @abstractmethod
    def get_filename_suggestion(self, extension: Optional[str], info: Optional[dict] = None) -> str:
        pass

    def open_settings_window(self, parent: Any) -> None:
        """
        Opens a settings window for this downloader source.
        Override this method if the source has configurable settings.
        """
        # Default implementation opens the main application preferences
        # Avoid circular import by importing inside the method
        from gi.repository import Gio
        action = Gio.SimpleAction.new("preferences", None)
        action.activate(None)
        # Alternatively, since we can't easily trigger the app action from here without the app instance context cleanly,
        # we can check if parent has the action or trigger it via the application.
        
        # A safer way if 'parent' is the window is to use the action group:
        if hasattr(parent, "get_application"):
            app = parent.get_application()
            if app:
                app.activate_action("preferences", None)


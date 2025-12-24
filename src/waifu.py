import requests
import json
from typing import Optional

from .types import NSFWOption
from .api_base import BaseDownloaderAPI

class WaifuDownloaderAPI(BaseDownloaderAPI):
    def __init__(self) -> None:
        super().__init__()
        self.endpoint = "https://api.waifu.im/search?is_nsfw="

    def get_page(self, nsfw: bool = False) -> Optional[str]:
        try:
            r = requests.get(self.endpoint + str(nsfw).lower(), timeout=10)
            if r.status_code == 200:
                return r.text
            else:
                return None
        except Exception as e:
            print(e)
            return None

    def get_page_url(self, response: Optional[str]) -> Optional[str]:
        if not response:
            return None
        try:
            data = json.loads(response)
            self.info = data
            return data["images"][0]['url']
        except Exception as e:
            print(e)
            return None

    def get_image_url(self, nsfw_mode: NSFWOption = NSFWOption.BLOCK_NSFW) -> Optional[str]:
        nsfw = False
        # Handle both Enum and string input
        if nsfw_mode == NSFWOption.ONLY_NSFW or nsfw_mode == NSFWOption.ONLY_NSFW.value:
            nsfw = True
        return self.get_page_url(self.get_page(nsfw))

    def get_artist(self, info: Optional[dict] = None) -> Optional[str]:
        data = info if info else self.info
        if not data:
            return None
        try:
            image_info = data['images'][0]
            artist = image_info.get('artist')
            if isinstance(artist, dict):
                return artist.get('name')
            return str(artist) if artist else None
        except Exception:
            return None

    def get_link(self, info: Optional[dict] = None) -> Optional[str]:
        data = info if info else self.info
        if not data:
            return None
        try:
            return data['images'][0].get('source')
        except Exception:
            return None

    def get_filename_suggestion(self, extension: Optional[str], info: Optional[dict] = None) -> str:
        data = info if info else self.info
        try:
            if data:
                image_id = data['images'][0].get('image_id', 'unknown')
            else:
                raise Exception("No info")
        except Exception:
            import time
            image_id = str(int(time.time()))
        
        if extension:
            return f"waifu.im_{image_id}.{extension}"
        return f"waifu.im_{image_id}"

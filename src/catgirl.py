import requests
import json
from typing import Optional

from .types import NSFWOption
from .api_base import BaseDownloaderAPI

class CatgirlDownloaderAPI(BaseDownloaderAPI):
    def __init__(self) -> None:
        super().__init__()
        self.endpoint = "https://nekos.moe/api/v1/random/image"

    def get_random_image_id(self, nsfw_mode: NSFWOption = NSFWOption.BLOCK_NSFW) -> Optional[str]:
        try:
            url = self.endpoint
            # Handle both Enum and string input
            if nsfw_mode == NSFWOption.ONLY_NSFW or nsfw_mode == NSFWOption.ONLY_NSFW.value:
                url += "?nsfw=true"
            elif nsfw_mode == NSFWOption.BLOCK_NSFW or nsfw_mode == NSFWOption.BLOCK_NSFW.value:
                url += "?nsfw=false"

            r = requests.get(url, timeout=10)
            if r.status_code != 200:
                return None
        except Exception as e:
            print(e)
            return None
        
        try:
            data = json.loads(r.text)
            self.info = data
            return data['images'][0]['id']
        except Exception:
            return None

    def get_image_url(self, nsfw_mode: NSFWOption = NSFWOption.BLOCK_NSFW) -> Optional[str]:
        image_id = self.get_random_image_id(nsfw_mode)
        if image_id:
            return "https://nekos.moe/image/" + image_id
        return None

    def get_artist(self, info: Optional[dict] = None) -> Optional[str]:
        data = info if info else self.info
        if not data:
            return None
        try:
            return data['images'][0]['artist']
        except Exception:
            return None

    def get_link(self, info: Optional[dict] = None) -> Optional[str]:
        data = info if info else self.info
        if not data:
            return None
        try:
            return "https://nekos.moe/post/" + data['images'][0]['id']
        except Exception:
            return None

    def get_filename_suggestion(self, extension: Optional[str], info: Optional[dict] = None) -> str:
        data = info if info else self.info
        if not data:
            import time
            image_id = str(int(time.time()))
        else:
            try:
                image_id = data["images"][0]["id"]
            except Exception:
                import time
                image_id = str(int(time.time()))
                
        if extension:
            return f"nekos.moe_{image_id}.{extension}"
        return f"nekos.moe_{image_id}"

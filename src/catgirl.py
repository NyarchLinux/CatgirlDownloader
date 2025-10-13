import requests
import json
from typing import Any

from .types import NSFWOption

class CatgirlDownloaderAPI:
    def __init__(self) -> None:
        self.endpoint = "https://nekos.moe/api/v1/random/image"

    def get_random_image_id(self, nsfw_mode: NSFWOption = NSFWOption.BLOCK_NSFW) -> str | None:
        try:
            url = self.endpoint
            if nsfw_mode == "Only NSFW":
                url += "?nsfw=true"
            elif nsfw_mode == "Block NSFW":
                url += "?nsfw=false"

            r = requests.get(url, timeout=10)
            if r.status_code != 200:
                return None
        except Exception as e:
            print(e)
            return None
        
        data = json.loads(r.text)
        self.info = data
        return data['images'][0]['id']

    def get_image_url(self, nsfw_mode: NSFWOption = NSFWOption.BLOCK_NSFW) -> str:
        return "https://nekos.moe/image/" + self.get_random_image_id(nsfw_mode)

    def get_image(self, url: str) -> bytes | Any:
        r = requests.get(url, timeout=20)
        return r.content

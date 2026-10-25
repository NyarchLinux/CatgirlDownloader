import requests
import json
import time
from typing import Optional

from .types import NSFWOption
from .api_base import BaseDownloaderAPI

_REQUEST_HEADERS = {
    "User-Agent": "CatgirlDownloader/1.0 (+https://github.com/NyarchLinux/CatgirlDownloader)"
}


class KitsuneDownloaderAPI(BaseDownloaderAPI):
    def __init__(self, settings=None) -> None:
        super().__init__()
        self.endpoint = "https://nekos.best/api/v2/kitsune"

    def get_request_headers(self) -> dict[str, str]:
        return dict(_REQUEST_HEADERS)

    def get_image_url(self, nsfw_mode: NSFWOption = NSFWOption.BLOCK_NSFW) -> Optional[str]:
        # nekos.best only serves SFW content, so nsfw_mode is intentionally ignored.
        try:
            r = requests.get(self.endpoint, headers=_REQUEST_HEADERS, timeout=10)
            if r.status_code != 200:
                return None
        except Exception as e:
            print(e)
            return None

        try:
            data = json.loads(r.text)
            self.info = data
            return data["results"][0]["url"]
        except Exception:
            return None

    def get_artist(self, info: Optional[dict] = None) -> Optional[str]:
        data = info if info else self.info
        if not data:
            return None
        try:
            return data["results"][0].get("artist_name")
        except Exception:
            return None

    def get_link(self, info: Optional[dict] = None) -> Optional[str]:
        data = info if info else self.info
        if not data:
            return None
        try:
            return data["results"][0].get("source_url")
        except Exception:
            return None

    def get_filename_suggestion(self, extension: Optional[str], info: Optional[dict] = None) -> str:
        data = info if info else self.info
        try:
            url = data["results"][0]["url"]
            image_id = url.rsplit("/", 1)[-1].rsplit(".", 1)[0]
        except Exception:
            image_id = str(int(time.time()))

        if extension:
            return f"nekos.best_{image_id}.{extension}"
        return f"nekos.best_{image_id}"

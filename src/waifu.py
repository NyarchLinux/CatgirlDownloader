import requests
import json
from typing import Optional

from .types import NSFWOption
from .api_base import BaseDownloaderAPI


class WaifuDownloaderAPI(BaseDownloaderAPI):
    def __init__(self, settings=None) -> None:
        super().__init__()
        self.endpoint = "https://api.waifu.im/images"
        self._settings = settings
        self.blacklist_tags = (
            settings.get_preference("blacklist_tags") if settings else ""
        )

    def get_page(self, nsfw: Optional[bool] = None) -> Optional[str]:
        try:
            params = {}

            if nsfw is None:
                params["IsNsfw"] = "All"
            elif nsfw:
                params["IsNsfw"] = "True"
            else:
                params["IsNsfw"] = "False"

            blacklist = self._parse_blacklist()
            for tag in blacklist:
                params["ExcludedTags"] = tag

            r = requests.get(self.endpoint, params=params, timeout=10)
            if r.status_code == 200:
                return r.text
            else:
                print(f"Waifu.im API returned status {r.status_code}")
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
            return data["items"][0]["url"]
        except Exception as e:
            print(e)
            return None

    def get_image_url(
        self, nsfw_mode: NSFWOption = NSFWOption.BLOCK_NSFW
    ) -> Optional[str]:
        nsfw = False
        if nsfw_mode == NSFWOption.ONLY_NSFW or nsfw_mode == NSFWOption.ONLY_NSFW.value:
            nsfw = True
        elif (
            nsfw_mode == NSFWOption.SHOW_EVERYTHING
            or nsfw_mode == NSFWOption.SHOW_EVERYTHING.value
        ):
            nsfw = None
        return self.get_page_url(self.get_page(nsfw))

    def get_artist(self, info: Optional[dict] = None) -> Optional[str]:
        data = info if info else self.info
        if not data:
            return None
        try:
            image_info = data["items"][0]
            artists = image_info.get("artists")
            if isinstance(artists, list) and artists:
                return artists[0].get("name")
            return None
        except Exception:
            return None

    def get_link(self, info: Optional[dict] = None) -> Optional[str]:
        data = info if info else self.info
        if not data:
            return None
        try:
            return data["items"][0].get("source")
        except Exception:
            return None

    def get_filename_suggestion(
        self, extension: Optional[str], info: Optional[dict] = None
    ) -> str:
        data = info if info else self.info
        image_id = self.get_filename_id(data.get("items")[0] if data else None)
        if extension:
            return f"waifu.im_{image_id}.{extension}"
        return f"waifu.im_{image_id}"

    def get_filename_id(self, info: dict = None) -> str:
        if info:
            return info.get("id", super().get_filename_id())
        return super().get_filename_id()

import requests
import json

class CatgirlDownloaderAPI:
    def __init__(self):
        self.endpoint = "https://nekos.moe/api/v1/random/image"
    def get_page(self, nsfw_mode = "Block NSFW"):
        try:
            url = self.endpoint
            if nsfw_mode == "Only NSFW":
                url += "?nsfw=true"
            elif nsfw_mode == "Block NSFW":
                url += "?nsfw=false"

            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                return r.text
            else:
                return None
        except Exception as e:
            print(e)
            return None

    def get_page_url(self, response):
        data = json.loads(response)
        self.info = data
        return "https://nekos.moe/image/" + data["images"][0]['id']

    def get_neko(self, nsfw_mode="Block NSFW"):
        return self.get_page_url(self.get_page(nsfw_mode))

    def get_image(self, url):
        r = requests.get(url, timeout=20)
        return r.content

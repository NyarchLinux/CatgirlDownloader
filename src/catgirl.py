import requests
import json

class CatgirlDownloaderAPI:
	def __init__(self):
		self.endpoint = "https://nekos.moe/api/v1/random/image?nsfw="
	def get_page(self, nsfw = False):
		try:
			r = requests.get(self.endpoint + str(nsfw).lower(), timeout=10)
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

	def get_neko(self, nsfw=False):
		return self.get_page_url(self.get_page(nsfw))

	def get_image(self, url):
		r = requests.get(url, timeout=20)
		return r.content


class E621DownloaderAPI:
	def __init__(self, user_agent: str = "FurryDownloader (by Avelcius)"):
		self.endpoint = "https://e621.net/posts.json"
		self.session = requests.Session()
		self.session.headers.update({
			"User-Agent": user_agent,
			"Accept": "application/json",
		})
		self.info = None

	def get_page(self, nsfw = False, tags: str = "", rating: str = None):
		try:
			query_tags = tags.strip()
			if rating in ("explicit", "questionable", "safe"):
				query_tags = (query_tags + f" rating:{rating}").strip()
			elif not nsfw:
				query_tags = (query_tags + " rating:safe").strip()
			params = {
				"limit": 1,
				"tags": ("order:random " + query_tags).strip(),
			}
			r = self.session.get(self.endpoint, params=params, timeout=12)
			if r.status_code == 200:
				return r.json()
			else:
				return None
		except Exception as e:
			print(e)
			return None

	def get_page_url(self, response_json):
		if (not response_json) or ("posts" not in response_json) or (len(response_json["posts"]) == 0):
			return None
		post = response_json["posts"][0]
		file_url = None
		if "file" in post:
			file_url = post["file"].get("url")
		artists = []
		if "tags" in post and "artist" in post["tags"]:
			artists = post["tags"]["artist"]
		artist_display = ", ".join(artists) if artists else "Unknown"
		post_id = str(post.get("id"))
		self.info = {"images": [{"id": post_id, "artist": artist_display}]}
		return file_url

	def get_neko(self, nsfw = False, tags: str = "", rating: str = None):
		return self.get_page_url(self.get_page(nsfw, tags, rating))

	def get_image(self, url):
		r = self.session.get(url, timeout=20)
		return r.content

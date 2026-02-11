from dataclasses import dataclass
from cachetools import TTLCache
import httpx


@dataclass
class ArticArtwork:
    external_id: int
    title: str | None


class ArticClient:
    BASE_URL = "https://api.artic.edu/api/v1"

    def __init__(self, timeout_seconds: float = 6.0, cache_ttl_seconds: int = 900):
        self._timeout = timeout_seconds
        self._cache = TTLCache(maxsize=5000, ttl=cache_ttl_seconds)

    def get_artwork(self, external_id: int) -> ArticArtwork | None:
        if external_id in self._cache:
            return self._cache[external_id]

        url = f"{self.BASE_URL}/artworks/{external_id}"
        try:
            r = httpx.get(url, timeout=self._timeout)
        except httpx.HTTPError:
            return None

        if r.status_code == 404:
            self._cache[external_id] = None
            return None

        if r.status_code != 200:
            return None

        data = r.json()
        title = None
        if isinstance(data, dict):
            d = data.get("data") or {}
            if isinstance(d, dict):
                title = d.get("title")

        artwork = ArticArtwork(external_id=external_id, title=title)
        self._cache[external_id] = artwork
        return artwork


artic_client = ArticClient()

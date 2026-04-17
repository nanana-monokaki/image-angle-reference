from __future__ import annotations
import httpx
from .base import Provider, ImageResult


class WallhavenProvider(Provider):
    """
    Wallhaven API (https://wallhaven.cc/api/v1/search)
    無認証・無料。categories=111 (general + anime + people), purity=100 (sfw only)。
    NSFW (purity=001) は API key が必要なため扱わない。
    """
    name = "Wallhaven"
    BASE = "https://wallhaven.cc/api/v1"

    def search(
        self,
        keyword: str,
        angle_tag: str,
        angle_text: str,
        safe: bool,
        limit: int = 20,
    ) -> list[ImageResult]:
        parts = [p for p in (keyword, angle_text) if p]
        q = " ".join(parts).strip()
        if not q:
            return []

        params = {
            "q": q,
            "categories": "111",
            "purity": "100" if safe else "110",
            "sorting": "relevance",
        }

        try:
            r = httpx.get(
                f"{self.BASE}/search",
                params=params,
                timeout=10.0,
                headers={"User-Agent": "image-angle-reference/0.1"},
            )
            r.raise_for_status()
            data = r.json()
        except Exception:
            return []

        out: list[ImageResult] = []
        for w in (data.get("data") or [])[:limit]:
            thumbs = w.get("thumbs") or {}
            thumb = thumbs.get("large") or thumbs.get("small") or thumbs.get("original")
            src = w.get("url")
            if not thumb or not src:
                continue
            out.append(
                ImageResult(
                    thumbnail_url=thumb,
                    source_url=src,
                    title=f"{(w.get('category') or 'image').title()} #{w.get('id')}",
                    author="Wallhaven",
                    source_name=self.name,
                    width=w.get("dimension_x") or 0,
                    height=w.get("dimension_y") or 0,
                )
            )
        return out

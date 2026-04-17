from __future__ import annotations
import httpx
from .base import Provider, ImageResult


class OpenverseProvider(Provider):
    """
    Openverse API (https://api.openverse.org)
    無認証・無料、CC ライセンスの画像。mature=false で安全フィルタ。
    """
    name = "Openverse"
    BASE = "https://api.openverse.org/v1"

    def search(
        self,
        keyword: str,
        angle_tag: str,
        angle_text: str,
        safe: bool,
        limit: int = 15,
    ) -> list[ImageResult]:
        parts = [p for p in (keyword, angle_text) if p]
        q = " ".join(parts).strip()
        if not q:
            return []

        try:
            r = httpx.get(
                f"{self.BASE}/images/",
                params={
                    "q": q,
                    "page_size": min(limit, 20),
                    "mature": "false" if safe else "true",
                },
                timeout=10.0,
                headers={"User-Agent": "image-angle-reference/0.1"},
            )
            r.raise_for_status()
            data = r.json()
        except Exception:
            return []

        out: list[ImageResult] = []
        for img in data.get("results", []):
            thumb = img.get("thumbnail") or img.get("url")
            src = img.get("foreign_landing_url") or img.get("url")
            if not thumb or not src:
                continue
            license_str = " ".join(
                s for s in (img.get("license"), img.get("license_version")) if s
            )
            out.append(
                ImageResult(
                    thumbnail_url=thumb,
                    source_url=src,
                    title=img.get("title") or "untitled",
                    author=img.get("creator") or "unknown",
                    source_name=self.name,
                    width=img.get("width") or 0,
                    height=img.get("height") or 0,
                    license=license_str,
                )
            )
        return out

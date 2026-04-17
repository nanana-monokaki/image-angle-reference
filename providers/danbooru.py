from __future__ import annotations
import httpx
from .base import Provider, ImageResult

SAFE_RATINGS = {"g", "s"}


class DanbooruProvider(Provider):
    """
    Danbooru 公式 API (無認証・無料)。
    無認証ユーザーは 1 検索につき最大 2 タグまで。
    safe フィルタはクライアント側で行う (rating g/s のみ通す)。
    """
    name = "Danbooru"
    BASE = "https://danbooru.donmai.us"

    def search(
        self,
        keyword: str,
        angle_tag: str,
        angle_text: str,
        safe: bool,
        limit: int = 20,
    ) -> list[ImageResult]:
        # ユーザー入力は最大 2 タグまで。それ以上あれば angle_tag は追加できない。
        user_tokens = keyword.strip().split()[:2] if keyword else []
        tags: list[str] = list(user_tokens)
        if angle_tag and len(tags) < 2:
            tags.append(angle_tag)
        tags = tags[:2]

        if not tags:
            return []

        fetch_limit = min(limit * 3 if safe else limit + 10, 100)

        try:
            r = httpx.get(
                f"{self.BASE}/posts.json",
                params={"tags": " ".join(tags), "limit": fetch_limit},
                timeout=10.0,
                headers={"User-Agent": "image-angle-reference/0.2"},
            )
            r.raise_for_status()
            data = r.json()
        except Exception:
            return []

        out: list[ImageResult] = []
        for post in data:
            if safe and post.get("rating") not in SAFE_RATINGS:
                continue
            thumb = post.get("preview_file_url") or post.get("file_url")
            if not thumb:
                continue
            artist = (post.get("tag_string_artist") or "unknown").split(" ")[0]
            character = (post.get("tag_string_character") or "").split(" ")[0]
            title = character.replace("_", " ") if character else f"Post #{post.get('id')}"
            out.append(
                ImageResult(
                    thumbnail_url=thumb,
                    source_url=f"{self.BASE}/posts/{post.get('id')}",
                    title=title,
                    author=artist.replace("_", " "),
                    source_name=self.name,
                    width=post.get("image_width", 0),
                    height=post.get("image_height", 0),
                )
            )
            if len(out) >= limit:
                break
        return out

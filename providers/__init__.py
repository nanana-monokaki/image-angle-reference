from .base import Provider, ImageResult
from .danbooru import DanbooruProvider
from .openverse import OpenverseProvider
from .wallhaven import WallhavenProvider

ALL_PROVIDERS: dict[str, type[Provider]] = {
    "Danbooru": DanbooruProvider,
    "Openverse": OpenverseProvider,
    "Wallhaven": WallhavenProvider,
}

__all__ = ["Provider", "ImageResult", "ALL_PROVIDERS"]

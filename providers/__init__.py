from .base import Provider, ImageResult
from .danbooru import DanbooruProvider
from .openverse import OpenverseProvider

ALL_PROVIDERS: dict[str, type[Provider]] = {
    "Danbooru": DanbooruProvider,
    "Openverse": OpenverseProvider,
}

__all__ = ["Provider", "ImageResult", "ALL_PROVIDERS"]

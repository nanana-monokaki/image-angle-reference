from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ImageResult:
    thumbnail_url: str
    source_url: str
    title: str
    author: str
    source_name: str
    width: int = 0
    height: int = 0
    license: str = ""


class Provider(ABC):
    name: str = ""

    @abstractmethod
    def search(
        self,
        keyword: str,
        angle_tag: str,
        angle_text: str,
        safe: bool,
        limit: int = 15,
    ) -> list[ImageResult]:
        ...

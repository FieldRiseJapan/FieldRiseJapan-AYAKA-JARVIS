"""Load approved mouth overlays independently from blink assets."""

from __future__ import annotations

from pathlib import Path

from PIL import Image


class MouthAssetLoader:
    def __init__(self, official_asset: Path):
        self.official_asset = official_asset

    def load(self) -> tuple[Image.Image | None, Image.Image | None]:
        directory = self.official_asset.parent / "animation" / "mouth"
        try:
            with Image.open(self.official_asset) as official:
                size = official.size
            closed = self._load(directory / "mouth_closed.png", size)
        except (OSError, ValueError):
            return None, None
        try:
            opened = self._load(directory / "mouth_open.png", size)
        except (OSError, ValueError):
            opened = None
        return closed, opened

    @staticmethod
    def _load(path: Path, size: tuple[int, int]) -> Image.Image:
        with Image.open(path) as source:
            if source.format != "PNG" or source.mode != "RGBA" or source.size != size:
                raise ValueError(f"invalid mouth overlay: {path.name}")
            overlay = source.copy()
        if overlay.getchannel("A").getextrema()[0] == 255:
            raise ValueError(f"mouth overlay lacks transparency: {path.name}")
        return overlay

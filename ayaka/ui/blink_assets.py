"""Safe loading and validation for approved AYAKA blink overlays."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image


@dataclass(frozen=True)
class BlinkAssets:
    """Validated eye overlays, or an explicit unavailable result."""

    available: bool
    half: Image.Image | None = None
    closed: Image.Image | None = None
    reason: str = ""
    mouth: Image.Image | None = None


class BlinkAssetLoader:
    """Load approved RGBA eye layers once and fail closed on invalid artwork."""

    HALF_NAME = "eyes_half.png"
    CLOSED_NAME = "eyes_closed.png"
    MOUTH_NAME = "mouth_closed.png"

    def __init__(self, official_asset: Path):
        self.official_asset = official_asset
        self._result: BlinkAssets | None = None

    @property
    def eyes_directory(self) -> Path:
        return self.official_asset.parent / "animation" / "eyes"

    @property
    def mouth_directory(self) -> Path:
        return self.official_asset.parent / "animation" / "mouth"

    def load(self) -> BlinkAssets:
        if self._result is not None:
            return self._result

        try:
            with Image.open(self.official_asset) as official:
                native_size = official.size
            half = self._load_overlay(self.eyes_directory / self.HALF_NAME, native_size)
            closed = self._load_overlay(self.eyes_directory / self.CLOSED_NAME, native_size)
            try:
                mouth = self._load_overlay(self.mouth_directory / self.MOUTH_NAME, native_size)
            except (OSError, ValueError):
                mouth = None
            self._result = BlinkAssets(True, half, closed, mouth=mouth)
        except (OSError, ValueError) as exc:
            self._result = BlinkAssets(False, reason=str(exc))
        return self._result

    @staticmethod
    def _load_overlay(path: Path, native_size: tuple[int, int]) -> Image.Image:
        if not path.is_file():
            raise ValueError(f"missing blink asset: {path.name}")
        with Image.open(path) as source:
            if source.format != "PNG":
                raise ValueError(f"blink asset is not PNG: {path.name}")
            if source.mode not in ("RGBA", "LA"):
                raise ValueError(f"blink asset has no alpha channel: {path.name}")
            if source.size != native_size:
                raise ValueError(
                    f"blink asset size mismatch: {path.name} ({source.size} != {native_size})"
                )
            overlay = source.convert("RGBA")
            if overlay.getchannel("A").getextrema()[0] == 255:
                raise ValueError(f"blink asset has no transparent pixels: {path.name}")
            return overlay

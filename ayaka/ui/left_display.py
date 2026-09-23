from __future__ import annotations

import math
from pathlib import Path
from typing import Any

try:
    import tkinter as tk
except ImportError:  # pragma: no cover - headless Linux validation
    tk = None

try:
    from PIL import Image, ImageTk
except ImportError:  # pragma: no cover - exercised only on an incomplete Windows install
    Image = None
    ImageTk = None


AYAKA_OFFICIAL_ASSET = Path("assets/characters/ayaka/ayaka_left_official.png")


def resolve_ayaka_asset(project_root: Path | None = None) -> Path:
    root = project_root or Path(__file__).resolve().parents[2]
    return root / AYAKA_OFFICIAL_ASSET


def fit_cover_size(source_size: tuple[int, int], target_size: tuple[int, int]) -> tuple[int, int]:
    source_width, source_height = source_size
    target_width, target_height = target_size
    if min(source_width, source_height, target_width, target_height) <= 0:
        raise ValueError("image and target dimensions must be positive")
    scale = max(target_width / source_width, target_height / source_height)
    return math.ceil(source_width * scale), math.ceil(source_height * scale)


def fit_contain_size(source_size: tuple[int, int], target_size: tuple[int, int]) -> tuple[int, int]:
    source_width, source_height = source_size
    target_width, target_height = target_size
    if min(source_width, source_height, target_width, target_height) <= 0:
        raise ValueError("image and target dimensions must be positive")
    scale = min(target_width / source_width, target_height / source_height)
    return max(1, math.floor(source_width * scale)), max(1, math.floor(source_height * scale))


class LeftDisplay:
    """AYAKA LEFT surface, isolated for a future Live2D/animated replacement."""

    def __init__(self, parent, monitor_size: tuple[int, int], asset_path: Path | None = None):
        self.parent = parent
        self.monitor_size = monitor_size
        self.asset_path = asset_path or resolve_ayaka_asset()
        self.image_label: Any = None
        self.fallback_frame: Any = None
        self._photo: ImageTk.PhotoImage | None = None

    @property
    def image_available(self) -> bool:
        return bool(Image is not None and ImageTk is not None and self.asset_path.is_file())

    def mount(self, fallback_factory) -> None:
        self.fallback_frame = fallback_factory(self.parent)
        self.fallback_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        if self.image_available:
            self._mount_image()
        else:
            self.fallback_frame.lift()

    def _mount_image(self) -> None:
        image = Image.open(self.asset_path).convert("RGB")
        resized_size = fit_contain_size(image.size, self.monitor_size)
        image = image.resize(resized_size, Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", self.monitor_size, (0, 0, 0))
        left = (self.monitor_size[0] - resized_size[0]) // 2
        top = (self.monitor_size[1] - resized_size[1]) // 2
        canvas.paste(image, (left, top))
        image = canvas
        self._photo = ImageTk.PhotoImage(image)
        self.image_label = tk.Label(self.parent, image=self._photo, borderwidth=0, highlightthickness=0)
        self.image_label.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.image_label.lower(self.fallback_frame)

    def show_ayaka(self) -> None:
        if self.image_label is not None and self.image_available:
            self.image_label.lift()
            if self.fallback_frame is not None:
                self.fallback_frame.lower(self.image_label)
        elif self.fallback_frame is not None:
            self.fallback_frame.lift()

    def show_fallback(self) -> None:
        if self.fallback_frame is not None:
            self.fallback_frame.lift()
        if self.image_label is not None:
            self.image_label.lower(self.fallback_frame)

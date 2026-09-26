from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from ..config import AnimationConfig
from .animation import AnimationController, AnimationFrame, BlinkPhase, MouthShape, CharacterAnimationProvider
from .blink_assets import BlinkAssetLoader
from .mouth_assets import MouthAssetLoader
from .left_hud import LeftHudOverlay
from .state import JarvisState

try:
    import tkinter as tk
except ImportError:  # pragma: no cover - headless Linux validation
    tk = None

try:
    from PIL import Image
except ImportError:  # pragma: no cover - exercised only on an incomplete Windows install
    Image = None

try:
    from PIL import ImageTk
except ImportError:  # pragma: no cover - exercised only on an incomplete Windows install
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


class StaticImageAnimationProvider:
    """Apply safe whole-character motion without altering image pixels."""

    def __init__(self, image_label: Any):
        self.image_label = image_label

    def apply(self, frame: AnimationFrame) -> None:
        self.image_label.place_configure(y=frame.vertical_offset_px)

    def reset(self) -> None:
        self.image_label.place_configure(y=0)


class BlinkOverlayAnimationProvider:
    """Composite approved eye overlays over an in-memory official-image copy."""

    def __init__(self, image_label, base_image, half_image, closed_image, *, mouth_closed=None, mouth_open=None, photo_factory=None):
        self.image_label = image_label
        self.base_image = base_image
        self.half_image = half_image
        self.closed_image = closed_image
        self._photo_factory = photo_factory or ImageTk.PhotoImage
        self._photo = None
        self._frames = {}
        for phase, eye in ((BlinkPhase.OPEN, None), (BlinkPhase.HALF, half_image), (BlinkPhase.CLOSED, closed_image)):
            eyed = base_image.convert("RGBA")
            if eye is not None:
                eyed = Image.alpha_composite(eyed, eye)
            closed = Image.alpha_composite(eyed, mouth_closed) if mouth_closed is not None else eyed
            self._frames[(phase, MouthShape.CLOSED)] = closed.convert("RGB")
            opened = Image.alpha_composite(eyed, mouth_open) if mouth_open is not None else closed
            self._frames[(phase, MouthShape.OPEN)] = opened.convert("RGB")
        self._photos = {}

    def apply(self, frame: AnimationFrame) -> None:
        key = (frame.blink_phase, MouthShape.OPEN if frame.speaking and frame.mouth_shape is MouthShape.OPEN else MouthShape.CLOSED)
        if key not in self._photos:
            self._photos[key] = self._photo_factory(self._frames[key])
        self._photo = self._photos[key]
        self.image_label.configure(image=self._photo)
        self.image_label.place_configure(y=frame.vertical_offset_px)

    def reset(self) -> None:
        key = (BlinkPhase.OPEN, MouthShape.CLOSED)
        if key not in self._photos:
            self._photos[key] = self._photo_factory(self._frames[key])
        self._photo = self._photos[key]
        self.image_label.configure(image=self._photo)
        self.image_label.place_configure(y=0)


class LeftDisplay:
    """AYAKA LEFT surface, isolated for a future Live2D/animated replacement."""

    def __init__(
        self,
        parent,
        monitor_size: tuple[int, int],
        asset_path: Path | None = None,
        animation_config: AnimationConfig | None = None,
        animation_provider: CharacterAnimationProvider | None = None,
    ):
        self.parent = parent
        self.monitor_size = monitor_size
        self.asset_path = asset_path or resolve_ayaka_asset()
        self.image_label: Any = None
        self.fallback_frame: Any = None
        self.hud = LeftHudOverlay(parent, monitor_size)
        self._photo: ImageTk.PhotoImage | None = None
        self._base_image: Any = None
        self._blink_loader = BlinkAssetLoader(self.asset_path)
        self._mouth_loader = MouthAssetLoader(self.asset_path)
        self.animation_controller = AnimationController(animation_config)
        self.animation_provider = animation_provider

    @property
    def image_available(self) -> bool:
        return bool(Image is not None and ImageTk is not None and self.asset_path.is_file())

    def mount(self, fallback_factory) -> None:
        self.fallback_frame = fallback_factory(self.parent)
        self.fallback_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        if self.image_available:
            try:
                self._mount_image()
                self.hud.mount()
            except (OSError, ValueError, RuntimeError):
                self.image_label = None
                self.animation_provider = None
                self.fallback_frame.lift()
        else:
            self.fallback_frame.lift()

    def _mount_image(self) -> None:
        with Image.open(self.asset_path) as source:
            native = source.convert("RGB")
        blink_assets = self._blink_loader.load() if self.animation_provider is None else None
        mouth_closed, mouth_open = self._mouth_loader.load() if self.animation_provider is None else (None, None)

        resized_size = fit_contain_size(native.size, self.monitor_size)
        left = (self.monitor_size[0] - resized_size[0]) // 2
        top = (self.monitor_size[1] - resized_size[1]) // 2

        def fitted(source, mode, background):
            canvas = Image.new(mode, self.monitor_size, background)
            canvas.paste(source.resize(resized_size, Image.Resampling.LANCZOS), (left, top))
            return canvas

        image = fitted(native, "RGB", (0, 0, 0))
        self._base_image = image.copy()
        fitted_mouth_closed = fitted(mouth_closed, "RGBA", (0, 0, 0, 0)) if mouth_closed is not None else None
        fitted_mouth_open = fitted(mouth_open, "RGBA", (0, 0, 0, 0)) if mouth_open is not None else None
        initial = Image.alpha_composite(image.convert("RGBA"), fitted_mouth_closed).convert("RGB") if fitted_mouth_closed is not None else image
        self._photo = ImageTk.PhotoImage(initial)
        self.image_label = tk.Label(self.parent, image=self._photo, borderwidth=0, highlightthickness=0)
        self.image_label.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.image_label.lower(self.fallback_frame)
        if self.animation_provider is None:
            if (blink_assets and blink_assets.available) or fitted_mouth_closed is not None:
                transparent = Image.new("RGBA", self.monitor_size, (0, 0, 0, 0))
                self.animation_provider = BlinkOverlayAnimationProvider(
                    self.image_label,
                    self._base_image,
                    fitted(blink_assets.half, "RGBA", (0, 0, 0, 0)) if blink_assets and blink_assets.available else transparent,
                    fitted(blink_assets.closed, "RGBA", (0, 0, 0, 0)) if blink_assets and blink_assets.available else transparent,
                    mouth_closed=fitted_mouth_closed,
                    mouth_open=fitted_mouth_open,
                )
            else:
                self.animation_provider = StaticImageAnimationProvider(self.image_label)

    def show_ayaka(self) -> None:
        if self.image_label is not None and self.image_available:
            self.image_label.lift()
            if self.fallback_frame is not None:
                self.fallback_frame.lower(self.image_label)
            self.hud.show()
        elif self.fallback_frame is not None:
            self.fallback_frame.lift()

    def show_fallback(self) -> None:
        self.reset_animation()
        if self.fallback_frame is not None:
            self.fallback_frame.lift()
        if self.image_label is not None:
            self.image_label.lower(self.fallback_frame)
        self.hud.hide()

    def update_state(self, state: JarvisState) -> None:
        self.hud.update(state)

    def animate(self, state: JarvisState) -> None:
        if self.animation_provider is None:
            return
        try:
            self.animation_provider.apply(self.animation_controller.update(state))
        except Exception:
            self.reset_animation()

    def reset_animation(self) -> None:
        self.animation_controller.reset()
        if self.animation_provider is None:
            return
        try:
            self.animation_provider.reset()
        except Exception:
            pass

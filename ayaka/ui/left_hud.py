"""State-driven LEFT HUD model and overlay."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

try:
    import tkinter as tk
except ImportError:  # pragma: no cover - headless validation
    tk = None

from .state import JarvisState


HUD_STATES = (
    JarvisState.LISTENING,
    JarvisState.THINKING,
    JarvisState.SPEAKING,
    JarvisState.EXECUTING,
)


@dataclass(frozen=True)
class HudStatusItem:
    state: JarvisState
    active: bool


@dataclass(frozen=True)
class HudStatusModel:
    items: tuple[HudStatusItem, ...]

    @classmethod
    def from_state(cls, state: JarvisState) -> "HudStatusModel":
        return cls(tuple(HudStatusItem(item_state, item_state is state) for item_state in HUD_STATES))


def calculate_hud_bounds(display_size: tuple[int, int]) -> tuple[int, int, int, int]:
    width, height = display_size
    if min(width, height) <= 0:
        raise ValueError("display dimensions must be positive")
    return (
        round(width * 0.08),
        round(height * 0.84),
        round(width * 0.92),
        round(height * 0.97),
    )


class LeftHudOverlay:
    """Tk overlay kept separate from the character-image renderer."""

    def __init__(self, parent: Any, display_size: tuple[int, int]):
        self.parent = parent
        self.display_size = display_size
        self.canvas: Any = None
        self._phase = False

    def mount(self) -> None:
        left, top, right, bottom = calculate_hud_bounds(self.display_size)
        self.canvas = tk.Canvas(
            self.parent,
            bg="#06101f",
            borderwidth=0,
            highlightthickness=1,
            highlightbackground="#16475b",
        )
        self.canvas.place(x=left, y=top, width=right - left, height=bottom - top)

    def update(self, state: JarvisState) -> None:
        if self.canvas is None:
            return
        self._phase = not self._phase
        self.canvas.delete("all")
        width = max(self.canvas.winfo_width(), 4)
        height = max(self.canvas.winfo_height(), 1)
        segment_width = width / len(HUD_STATES)
        font_size = max(10, min(18, height // 7))
        for index, item in enumerate(HudStatusModel.from_state(state).items):
            x1 = round(index * segment_width) + 5
            x2 = round((index + 1) * segment_width) - 5
            active_outline = "#baf8ff" if self._phase else "#56e7ff"
            outline = active_outline if item.active else "#245064"
            fill = "#0b3d52" if item.active else "#081927"
            text_color = "#e8fdff" if item.active else "#597989"
            line_width = 4 if item.active else 1
            self.canvas.create_rectangle(
                x1,
                6,
                x2,
                height - 7,
                fill=fill,
                outline=outline,
                width=line_width,
            )
            if item.active:
                self.canvas.create_rectangle(
                    x1 + 6,
                    12,
                    x2 - 6,
                    height - 13,
                    outline="#27d9ff",
                    width=1,
                )
            self.canvas.create_text(
                (x1 + x2) / 2,
                height / 2,
                text=item.state.value,
                fill=text_color,
                font=("Consolas", font_size, "bold" if item.active else "normal"),
            )

    def show(self) -> None:
        if self.canvas is not None:
            left, top, right, bottom = calculate_hud_bounds(self.display_size)
            self.canvas.place(x=left, y=top, width=right - left, height=bottom - top)
            self.canvas.lift()

    def hide(self) -> None:
        if self.canvas is not None:
            self.canvas.place_forget()

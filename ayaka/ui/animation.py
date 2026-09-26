"""Renderer-neutral character animation state and timing."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
import math
import random
import time
from typing import Protocol

from ..config import AnimationConfig
from .state import JarvisState
from .voice_sync import WINDOW_SECONDS, OPEN_HOLD_SECONDS, CLOSED_HOLD_SECONDS


class BlinkPhase(str, Enum):
    OPEN = "OPEN"
    HALF = "HALF"
    CLOSED = "CLOSED"


class MouthShape(str, Enum):
    CLOSED = "CLOSED"
    SMALL = "SMALL"
    MEDIUM = "MEDIUM"
    OPEN = "OPEN"


@dataclass(frozen=True)
class AnimationFrame:
    state: JarvisState
    vertical_offset_px: int = 0
    blink_phase: BlinkPhase = BlinkPhase.OPEN
    mouth_open: float = 0.0
    speaking: bool = False
    mouth_shape: MouthShape = MouthShape.CLOSED


class CharacterAnimationProvider(Protocol):
    def apply(self, frame: AnimationFrame) -> None: ...

    def reset(self) -> None: ...


class AnimationController:
    """Produce animation signals without knowing how a character is rendered."""

    HALF_CLOSE_SECONDS = 0.08
    CLOSED_SECONDS = 0.12
    HALF_OPEN_SECONDS = 0.08
    MOUTH_INTERVAL_SECONDS = 0.18

    def __init__(
        self,
        config: AnimationConfig | None = None,
        *,
        clock: Callable[[], float] = time.monotonic,
        blink_interval: Callable[[], float] | None = None,
    ):
        self.config = config or AnimationConfig()
        self._clock = clock
        self._blink_interval = blink_interval or (lambda: random.uniform(3.5, 6.5))
        self._started_at = self._clock()
        self._next_blink_at = self._started_at + max(0.1, self._blink_interval())
        self._state = JarvisState.STANDBY
        self._speaking_level = 0.0
        self._speaking_started_at: float | None = None
        self._voice_envelope: tuple[float, ...] | None = None
        self._voice_started_at = 0.0
        self._voice_duration = 0.0
        self._voice_threshold = 0.0
        self._voice_mouth = MouthShape.CLOSED
        self._mouth_changed_at = 0.0

    def set_voice_envelope(self, values: tuple[float, ...], duration: float, threshold: float, started_at: float) -> None:
        if not values or duration <= 0 or threshold <= 0 or not all(math.isfinite(v) and v >= 0 for v in (*values, duration, threshold, started_at)):
            raise ValueError("invalid voice envelope")
        self._voice_envelope = values
        self._voice_duration = duration
        self._voice_threshold = threshold
        self._voice_started_at = started_at
        self._voice_mouth = MouthShape.CLOSED
        self._mouth_changed_at = started_at - CLOSED_HOLD_SECONDS

    def clear_voice_envelope(self) -> None:
        self._voice_envelope = None
        self._voice_mouth = MouthShape.CLOSED

    def set_speaking_level(self, level: float) -> None:
        try:
            value = float(level)
            self._speaking_level = min(1.0, max(0.0, value)) if math.isfinite(value) else 0.0
        except (TypeError, ValueError):
            self._speaking_level = 0.0

    def reset(self) -> None:
        self.clear_voice_envelope()
        self._speaking_level = 0.0
        self._speaking_started_at = None
        self._state = JarvisState.STANDBY
        self._started_at = self._clock()
        self._next_blink_at = self._started_at + max(0.1, self._blink_interval())

    def update(self, state: JarvisState, *, now: float | None = None) -> AnimationFrame:
        current_time = self._clock() if now is None else now
        if self._state is JarvisState.SPEAKING and state is not JarvisState.SPEAKING:
            self._speaking_level = 0.0
            self._speaking_started_at = None
            self.clear_voice_envelope()
        elif self._state is not JarvisState.SPEAKING and state is JarvisState.SPEAKING:
            self._speaking_started_at = current_time
        self._state = state
        speaking = self.config.enabled and state is JarvisState.SPEAKING
        level = self._speaking_level if speaking and self.config.lipsync_enabled else 0.0
        return AnimationFrame(
            state=state,
            vertical_offset_px=self._breathing_offset(current_time) if self.config.enabled else 0,
            blink_phase=self._blink_phase(current_time) if self.config.enabled and self.config.blink_enabled else BlinkPhase.OPEN,
            mouth_open=level,
            speaking=speaking,
            mouth_shape=(self._voice_mouth_at(current_time) if self._voice_envelope is not None else self._timed_mouth(current_time))
            if speaking and self.config.lipsync_enabled else MouthShape.CLOSED,
        )

    def _voice_mouth_at(self, now: float) -> MouthShape:
        elapsed = now - self._voice_started_at
        if elapsed < 0 or elapsed + 1e-9 >= self._voice_duration:
            self._voice_mouth = MouthShape.CLOSED
            return MouthShape.CLOSED
        index = min(int((elapsed + 1e-9) / WINDOW_SECONDS), len(self._voice_envelope) - 1)
        desired = MouthShape.OPEN if self._voice_envelope[index] >= self._voice_threshold else MouthShape.CLOSED
        hold = OPEN_HOLD_SECONDS if self._voice_mouth is MouthShape.OPEN else CLOSED_HOLD_SECONDS
        if desired is not self._voice_mouth and now - self._mouth_changed_at >= hold:
            self._voice_mouth = desired
            self._mouth_changed_at = now
        return self._voice_mouth

    def _timed_mouth(self, now: float) -> MouthShape:
        if self._speaking_started_at is None:
            return MouthShape.CLOSED
        elapsed = max(0.0, now - self._speaking_started_at)
        return MouthShape.OPEN if int(elapsed / self.MOUTH_INTERVAL_SECONDS) % 2 else MouthShape.CLOSED

    @staticmethod
    def _mouth_shape(level: float) -> MouthShape:
        if level <= 0:
            return MouthShape.CLOSED
        if level < 0.33:
            return MouthShape.SMALL
        if level < 0.66:
            return MouthShape.MEDIUM
        return MouthShape.OPEN

    def _breathing_offset(self, now: float) -> int:
        amplitude = self.config.safe_breathing_amplitude_px
        period = self.config.breathing_period_seconds
        if not self.config.breathing_enabled or amplitude == 0 or period <= 0:
            return 0
        phase = ((now - self._started_at) / period) * math.tau
        return round(amplitude * math.sin(phase))

    def _blink_phase(self, now: float) -> BlinkPhase:
        half_closed_at = self._next_blink_at + self.HALF_CLOSE_SECONDS
        closed_until = half_closed_at + self.CLOSED_SECONDS
        reopened_at = closed_until + self.HALF_OPEN_SECONDS
        if now < self._next_blink_at:
            return BlinkPhase.OPEN
        if now < half_closed_at:
            return BlinkPhase.HALF
        if now < closed_until:
            return BlinkPhase.CLOSED
        if now < reopened_at:
            return BlinkPhase.HALF
        self._next_blink_at = now + max(0.1, self._blink_interval())
        return BlinkPhase.OPEN

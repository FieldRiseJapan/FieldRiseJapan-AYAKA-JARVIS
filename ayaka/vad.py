from collections import deque

import numpy as np

from .config import VadConfig


class VadSegmenter:
    """Turn fixed-size PCM chunks into speech segments using RMS level."""

    def __init__(self, config: VadConfig, sample_rate: int):
        if sample_rate <= 0:
            raise ValueError("sample_rate must be positive")
        if config.threshold < 0 or config.silence_seconds <= 0 or config.max_record_seconds <= 0:
            raise ValueError("VAD threshold and durations must be positive or zero as appropriate")
        self.config = config
        self.sample_rate = sample_rate
        self.state = "waiting"
        self.frames_collected = 0
        self.silent_frames = 0
        self._chunks: list[np.ndarray] = []
        self._pre_roll: deque[np.ndarray] = deque()
        self._pre_roll_frames = 0

    @staticmethod
    def rms(chunk: np.ndarray) -> float:
        values = np.asarray(chunk, dtype=np.float32).reshape(-1)
        if values.size == 0:
            return 0.0
        return float(np.sqrt(np.mean(values * values)))

    def _reset(self) -> None:
        self.state = "waiting"
        self.frames_collected = 0
        self.silent_frames = 0
        self._chunks = []

    def _remember_pre_roll(self, chunk: np.ndarray) -> None:
        self._pre_roll.append(chunk.copy())
        self._pre_roll_frames += len(chunk)
        target = int(self.config.pre_roll_seconds * self.sample_rate)
        while self._pre_roll and self._pre_roll_frames - len(self._pre_roll[0]) >= target:
            self._pre_roll_frames -= len(self._pre_roll.popleft())

    def _finish(self) -> np.ndarray | None:
        if self.state != "recording" or not self._chunks:
            self._reset()
            return None
        segment = np.concatenate(self._chunks)
        self._reset()
        return segment

    def feed(self, chunk: np.ndarray) -> np.ndarray | None:
        values = np.asarray(chunk, dtype=np.int16).reshape(-1)
        if values.size == 0:
            return None
        level = self.rms(values)
        voiced = level >= self.config.threshold

        if self.state == "waiting":
            if voiced:
                self.state = "recording"
                self._chunks = list(self._pre_roll)
                self.frames_collected = self._pre_roll_frames
                self._pre_roll.clear()
                self._pre_roll_frames = 0
                self.silent_frames = 0
                self._chunks.append(values.copy())
                self.frames_collected += len(values)
            else:
                self._remember_pre_roll(values)
            return None

        self._chunks.append(values.copy())
        self.frames_collected += len(values)
        if voiced:
            self.silent_frames = 0
        else:
            self.silent_frames += len(values)

        if self.silent_frames >= int(self.config.silence_seconds * self.sample_rate):
            return self._finish()
        if self.frames_collected >= int(self.config.max_record_seconds * self.sample_rate):
            return self._finish()
        return None

    def flush(self) -> np.ndarray | None:
        """Finish an active segment; waiting/no-speech produces no segment."""
        return self._finish()

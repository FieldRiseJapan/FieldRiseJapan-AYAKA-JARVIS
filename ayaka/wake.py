import re
import unicodedata


class WakeWordDetector:
    def __init__(self, wake_words: list[str] | tuple[str, ...]):
        self.wake_words = tuple(self._normalize(word) for word in wake_words if word.strip())
        if not self.wake_words:
            raise ValueError("At least one wake word is required")

    @staticmethod
    def _normalize(text: str) -> str:
        return re.sub(r"\s+", "", unicodedata.normalize("NFKC", text)).casefold()

    def detect(self, transcript: str) -> bool:
        normalized = self._normalize(transcript)
        return any(word in normalized for word in self.wake_words)

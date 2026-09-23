from enum import Enum
import re
import unicodedata


class Intent(str, Enum):
    WAKE = "WAKE"
    SLEEP = "SLEEP"
    AYAKA_MODE = "AYAKA_MODE"
    MOMOKA_MODE = "MOMOKA_MODE"
    HOME = "HOME"
    BACK = "BACK"
    SNS = "SNS"
    SOUNDON = "SOUNDON"
    GITHUB = "GITHUB"
    UNKNOWN = "UNKNOWN"


# Keep real-device Whisper name variants separate from ordinary commands so
# future field-log additions remain easy to review and do not broaden commands.
MOMOKA_NAME_ALIASES = (
    "桃花", "ももか", "モモカ", "もも", "モモ", "まもか", "まもかぁ",
    "ももかわ", "モモカー", "もうもう", "もうもうか", "モモンカー",
    "モンモンカー", "おもが",
)
AYAKA_NAME_ALIASES = (
    "彩花", "あやか", "アヤカ", "あやかぁ", "あや", "アヤ", "おやか",
    "あうや", "アイアー",
)
NAME_MODE_ALIASES = {
    Intent.MOMOKA_MODE: MOMOKA_NAME_ALIASES,
    Intent.AYAKA_MODE: AYAKA_NAME_ALIASES,
}


def normalize_transcript(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return re.sub(r"[\s。、！？!?.,:：；;「」『』（）()]+", "", normalized)


class CommandRouter:
    _aliases = {
        Intent.WAKE: ("おはよう",),
        Intent.SLEEP: ("おやすみ",),
        **NAME_MODE_ALIASES,
        Intent.HOME: ("ホーム",),
        Intent.BACK: ("戻って",),
        Intent.SNS: ("sns見せて", "sns出して", "snsのデータ見せて"),
        Intent.SOUNDON: ("soundon見せて", "soundon出して", "サウンドオン見せて", "サウンドオン出して", "収益見せて"),
        Intent.GITHUB: ("github見せて", "github出して", "ギットハブ見せて", "ギットハブ出して"),
    }

    def __init__(self):
        self._lookup = {
            normalize_transcript(alias): intent
            for intent, aliases in self._aliases.items()
            for alias in aliases
        }

    def route(self, transcript: str) -> Intent:
        return self._lookup.get(normalize_transcript(transcript), Intent.UNKNOWN)

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


def normalize_transcript(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return re.sub(r"[\s。、！？!?.,:：；;「」『』（）()]+", "", normalized)


class CommandRouter:
    _aliases = {
        Intent.WAKE: ("おはよう",),
        Intent.SLEEP: ("おやすみ",),
        Intent.AYAKA_MODE: ("彩花", "あや"),
        Intent.MOMOKA_MODE: ("桃花", "もも"),
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

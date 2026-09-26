from typing import Protocol


class BrainProvider(Protocol):
    def respond(self, transcript: str) -> str | None: ...


class FallbackProvider:
    def respond(self, transcript: str) -> str:
        return "社長、会話機能は現在準備中です。"

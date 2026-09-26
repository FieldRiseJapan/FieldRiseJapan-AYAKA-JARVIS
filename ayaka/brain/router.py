from dataclasses import dataclass
from enum import Enum

from ..commands import CommandRouter, Intent


class BrainRouteKind(str, Enum):
    COMMAND = "COMMAND"
    CONVERSATION = "CONVERSATION"


@dataclass(frozen=True)
class BrainRouteResult:
    kind: BrainRouteKind
    intent: Intent = Intent.UNKNOWN


class BrainRouter:
    def __init__(self, commands: CommandRouter | None = None):
        self.commands = commands or CommandRouter()

    def route(self, transcript: str) -> BrainRouteResult:
        intent = self.commands.route(transcript)
        if intent is Intent.UNKNOWN:
            return BrainRouteResult(BrainRouteKind.CONVERSATION)
        return BrainRouteResult(BrainRouteKind.COMMAND, intent)

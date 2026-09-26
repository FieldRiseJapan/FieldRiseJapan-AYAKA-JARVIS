"""Small UI-thread coordinator; provider work always runs off the Tk thread."""

import threading

from .router import BrainRouteKind, BrainRouter
from .provider import BrainProvider
from ..ui.state import JarvisMode


class BrainFlow:
    def __init__(self, router: BrainRouter, provider: BrainProvider, mode, voice_flow,
                 schedule, on_command, on_response, events):
        self.router = router
        self.provider = provider
        self.mode = mode
        self.voice_flow = voice_flow
        self.schedule = schedule
        self.on_command = on_command
        self.on_response = on_response
        self.events = events
        self.generation = 0

    def invalidate(self):
        self.generation += 1

    def transcript(self, text: str, hold_ms: int):
        self.invalidate()
        generation = self.generation
        self.voice_flow.transcript_received()
        self.schedule(hold_ms, lambda: self._route(text, generation, hold_ms))

    def _route(self, text: str, generation: int, hold_ms: int):
        if generation != self.generation:
            return
        result = self.router.route(text)
        if result.kind is BrainRouteKind.COMMAND:
            self.voice_flow.begin_execution()
            self.schedule(hold_ms, lambda: self._dispatch(result.intent, generation))
        elif self.mode() is JarvisMode.AYAKA:
            threading.Thread(target=self._respond, args=(text, generation), daemon=True).start()
        else:
            self.voice_flow.speech_completed()

    def _dispatch(self, intent, generation: int):
        if generation == self.generation:
            self.invalidate()  # Cancel pending conversations, including on mode changes / exit.
            self.on_command(intent)

    def _respond(self, text: str, generation: int):
        try:
            response = self.provider.respond(text)
        except Exception:
            response = None
        self.events.put(("brain_response", (generation, response)))

    def complete(self, generation: int, response: str | None):
        if generation != self.generation or self.mode() is not JarvisMode.AYAKA:
            return
        if response and response.strip():
            self.on_response(response)
        else:
            self.voice_flow.speech_completed()

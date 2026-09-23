"""Voice-pipeline state transitions shared by UI integrations."""

from __future__ import annotations

from .state import JarvisState, UiState


class VoiceUiFlow:
    def __init__(self, state: UiState):
        self.state = state

    def begin_listening(self) -> None:
        self.state.set_system_state(JarvisState.LISTENING)

    def transcript_received(self) -> None:
        self.state.set_system_state(JarvisState.THINKING)

    def begin_execution(self) -> None:
        self.state.set_system_state(JarvisState.EXECUTING)

    def begin_speaking(self) -> None:
        self.state.set_system_state(JarvisState.SPEAKING)

    def speech_completed(self) -> None:
        self.begin_listening()

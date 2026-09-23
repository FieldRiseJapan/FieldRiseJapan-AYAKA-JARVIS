from collections.abc import Callable

from ..commands import Intent
from .state import DashboardPage, JarvisMode, JarvisState, UiState


class JarvisController:
    def __init__(self, state: UiState | None = None, on_close: Callable[[], None] | None = None):
        self.state = state or UiState()
        self.on_close = on_close

    def dispatch(self, intent: Intent) -> str | None:
        if intent is Intent.WAKE:
            self.state.set_mode(JarvisMode.AYAKA)
            self.state.set_system_state(JarvisState.COMPLETE)
            return "おはようございます、社長。"
        if intent is Intent.SLEEP:
            self.state.set_system_state(JarvisState.COMPLETE)
            if self.on_close:
                self.on_close()
            return "おやすみなさい、社長。"
        if intent is Intent.AYAKA_MODE:
            self.state.set_mode(JarvisMode.AYAKA)
            return None
        if intent is Intent.MOMOKA_MODE:
            self.state.set_mode(JarvisMode.MOMOKA)
            return None
        if intent is Intent.HOME:
            self.state.navigate(DashboardPage.HOME)
            return None
        if intent is Intent.BACK:
            self.state.back()
            return None
        page_by_intent = {
            Intent.SNS: DashboardPage.SNS,
            Intent.SOUNDON: DashboardPage.SOUNDON,
            Intent.GITHUB: DashboardPage.GITHUB,
        }
        if intent in page_by_intent:
            self.state.navigate(page_by_intent[intent])
        return None

from dataclasses import dataclass, field
from enum import Enum


class JarvisMode(str, Enum):
    AYAKA = "AYAKA"
    MOMOKA = "MOMOKA"


class JarvisState(str, Enum):
    STANDBY = "STANDBY"
    LISTENING = "LISTENING"
    THINKING = "THINKING"
    SPEAKING = "SPEAKING"
    EXECUTING = "EXECUTING"
    COMPLETE = "COMPLETE"


class DashboardPage(str, Enum):
    HOME = "HOME"
    SNS = "SNS"
    SOUNDON = "SOUNDON"
    GITHUB = "GITHUB"


@dataclass
class UiState:
    mode: JarvisMode = JarvisMode.AYAKA
    system_state: JarvisState = JarvisState.STANDBY
    page: DashboardPage = DashboardPage.HOME
    _history: list[DashboardPage] = field(default_factory=list)

    @property
    def active_character(self) -> str:
        return self.mode.value

    @property
    def theme_accent(self) -> str:
        return "#b56cff" if self.mode is JarvisMode.MOMOKA else "#27d9ff"

    @property
    def theme_name(self) -> str:
        return "MOMOKA PURPLE" if self.mode is JarvisMode.MOMOKA else "AYAKA BLUE"

    def set_mode(self, mode: JarvisMode) -> None:
        self.mode = mode

    def set_system_state(self, state: JarvisState) -> None:
        self.system_state = state

    def navigate(self, page: DashboardPage) -> None:
        if page is self.page:
            return
        self._history.append(self.page)
        self.page = page

    def back(self) -> DashboardPage:
        if self._history:
            self.page = self._history.pop()
        return self.page

import unittest

from ayaka.ui.monitors import MonitorInfo, assign_monitors
from ayaka.ui.state import DashboardPage, JarvisMode, JarvisState, UiState


class MonitorAssignmentTests(unittest.TestCase):
    def test_primary_and_portrait_landscape_monitors_are_assigned(self):
        monitors = [
            MonitorInfo("right", 1920, 0, 1920, 1080, False),
            MonitorInfo("left", 0, 0, 1920, 1080, True),
            MonitorInfo("center", -1080, 0, 1080, 1920, False),
        ]
        layout = assign_monitors(monitors)
        self.assertEqual(layout.left.name, "left")
        self.assertEqual(layout.center.name, "center")
        self.assertEqual(layout.right.name, "right")

    def test_single_monitor_fills_all_roles_without_crashing(self):
        monitor = MonitorInfo("only", 0, 0, 1920, 1080, True)
        layout = assign_monitors([monitor])
        self.assertEqual(layout.left.name, "only")
        self.assertEqual(layout.center.name, "only")
        self.assertEqual(layout.right.name, "only")


class UiStateTests(unittest.TestCase):
    def test_mode_switch_changes_theme_and_active_character(self):
        state = UiState()
        self.assertEqual(state.mode, JarvisMode.AYAKA)
        state.set_mode(JarvisMode.MOMOKA)
        self.assertEqual(state.mode, JarvisMode.MOMOKA)
        self.assertEqual(state.theme_accent, "#b56cff")
        self.assertEqual(state.active_character, "MOMOKA")

    def test_navigation_back_returns_to_previous_page(self):
        state = UiState()
        state.navigate(DashboardPage.SNS)
        state.navigate(DashboardPage.SOUNDON)
        self.assertEqual(state.page, DashboardPage.SOUNDON)
        state.back()
        self.assertEqual(state.page, DashboardPage.SNS)
        state.back()
        self.assertEqual(state.page, DashboardPage.HOME)

    def test_system_state_is_explicit(self):
        state = UiState()
        state.set_system_state(JarvisState.LISTENING)
        self.assertEqual(state.system_state, JarvisState.LISTENING)


if __name__ == "__main__":
    unittest.main()

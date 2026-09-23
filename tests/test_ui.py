import unittest
import ctypes

from ayaka.ui.app import monitor_geometry
from ayaka.ui.monitors import MonitorInfo, MonitorInfoStructure, assign_monitors
from ayaka.ui.state import DashboardPage, JarvisMode, JarvisState, UiState
from ayaka.ui.voice_flow import VoiceUiFlow


class MonitorAssignmentTests(unittest.TestCase):
    def test_win32_monitor_info_structure_has_required_fields(self):
        field_names = [name for name, _type in MonitorInfoStructure._fields_]
        self.assertEqual(field_names, ["cbSize", "rcMonitor", "rcWork", "dwFlags"])
        self.assertGreater(ctypes.sizeof(MonitorInfoStructure), 0)

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

    def test_win32_work_area_drives_window_geometry(self):
        monitor = MonitorInfo(
            "center", -1080, 0, 1080, 1920, False,
            work_x=-1080, work_y=40, work_width=1080, work_height=1840,
        )

        self.assertEqual(monitor.work_area, (-1080, 40, 1080, 1840))
        self.assertEqual(monitor_geometry(monitor), "1080x1840-1080+40")


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

    def test_voice_flow_exposes_each_operational_state_in_order(self):
        state = UiState()
        flow = VoiceUiFlow(state)

        observed = []
        for transition in (
            flow.begin_listening,
            flow.transcript_received,
            flow.begin_execution,
            flow.begin_speaking,
            flow.speech_completed,
        ):
            transition()
            observed.append(state.system_state)

        self.assertEqual(
            observed,
            [
                JarvisState.LISTENING,
                JarvisState.THINKING,
                JarvisState.EXECUTING,
                JarvisState.SPEAKING,
                JarvisState.LISTENING,
            ],
        )


if __name__ == "__main__":
    unittest.main()

import unittest
from pathlib import Path

from ayaka.ui.left_display import (
    AYAKA_OFFICIAL_ASSET,
    LeftDisplay,
    StaticImageAnimationProvider,
    fit_contain_size,
    fit_cover_size,
    resolve_ayaka_asset,
)
from ayaka.ui.left_hud import (
    HUD_STATES,
    HudStatusModel,
    LeftHudOverlay,
    calculate_hud_bounds,
)
from ayaka.ui.animation import AnimationFrame, BlinkPhase
from ayaka.ui.state import JarvisState
from ayaka.ui.monitors import MonitorInfo


class LeftDisplayAssetTests(unittest.TestCase):
    def test_official_asset_is_at_the_stable_repository_path(self):
        project_root = Path(__file__).parents[1]
        asset = resolve_ayaka_asset(project_root)
        self.assertEqual(asset.relative_to(project_root), AYAKA_OFFICIAL_ASSET)
        self.assertTrue(asset.is_file())

    def test_cover_size_fills_2560_by_1440_without_distorting_ratio(self):
        scaled = fit_cover_size((1672, 941), (2560, 1440))
        self.assertGreaterEqual(scaled[0], 2560)
        self.assertGreaterEqual(scaled[1], 1440)
        self.assertAlmostEqual(scaled[0] / scaled[1], 1672 / 941, places=3)

    def test_missing_asset_is_detected_for_fallback(self):
        missing = resolve_ayaka_asset(Path("/tmp/does-not-exist-ayaka-project"))
        self.assertFalse(missing.is_file())

    def test_work_area_target_keeps_full_image_visible(self):
        scaled = fit_contain_size((1672, 941), (2560, 1400))
        self.assertLessEqual(scaled[0], 2560)
        self.assertLessEqual(scaled[1], 1400)
        self.assertAlmostEqual(scaled[0] / scaled[1], 1672 / 941, places=3)

    def test_monitor_work_area_is_dynamic_and_not_hardcoded(self):
        monitor = MonitorInfo("left", 0, 0, 2560, 1440, True, 0, 0, 2560, 1400)
        self.assertEqual(monitor.work_area, (0, 0, 2560, 1400))


class StaticImageAnimationProviderTests(unittest.TestCase):
    def test_provider_applies_only_whole_character_vertical_offset(self):
        class FakeLabel:
            def __init__(self):
                self.placements = []

            def place_configure(self, **kwargs):
                self.placements.append(kwargs)

        label = FakeLabel()
        provider = StaticImageAnimationProvider(label)
        frame = AnimationFrame(
            state=JarvisState.SPEAKING,
            vertical_offset_px=2,
            blink_phase=BlinkPhase.CLOSED,
            mouth_open=1.0,
            speaking=True,
        )

        provider.apply(frame)
        provider.reset()

        self.assertEqual(label.placements, [{"y": 2}, {"y": 0}])

    def test_animation_provider_failure_is_contained_and_reset(self):
        class RaisingProvider:
            def __init__(self):
                self.reset_count = 0

            def apply(self, _frame):
                raise RuntimeError("renderer unavailable")

            def reset(self):
                self.reset_count += 1

        provider = RaisingProvider()
        display = LeftDisplay(
            parent=None,
            monitor_size=(1920, 1040),
            animation_provider=provider,
        )

        display.animate(JarvisState.LISTENING)

        self.assertEqual(provider.reset_count, 1)

    def test_fallback_resets_character_offset(self):
        class RecordingProvider:
            def __init__(self):
                self.reset_count = 0

            def apply(self, _frame):
                pass

            def reset(self):
                self.reset_count += 1

        provider = RecordingProvider()
        display = LeftDisplay(
            parent=None,
            monitor_size=(1920, 1040),
            animation_provider=provider,
        )

        display.show_fallback()

        self.assertEqual(provider.reset_count, 1)


class LeftHudTests(unittest.TestCase):
    def test_show_raises_canvas_widget_without_calling_canvas_item_lift(self):
        class FakeTk:
            def __init__(self):
                self.calls = []

            def call(self, *args):
                self.calls.append(args)

        class FakeCanvas:
            _w = ".!canvas"

            def __init__(self):
                self.tk = FakeTk()
                self.placements = []

            def place(self, **kwargs):
                self.placements.append(kwargs)

            def lift(self):
                raise AssertionError("Canvas.lift() raises canvas items, not the widget")

        overlay = LeftHudOverlay(parent=None, display_size=(1000, 500))
        overlay.canvas = FakeCanvas()

        overlay.show()

        self.assertEqual(
            overlay.canvas.placements,
            [{"x": 80, "y": 420, "width": 840, "height": 65}],
        )
        self.assertEqual(overlay.canvas.tk.calls, [("raise", ".!canvas", None)])

    def test_only_current_operational_state_is_active(self):
        model = HudStatusModel.from_state(JarvisState.THINKING)

        self.assertEqual([item.state for item in model.items], list(HUD_STATES))
        self.assertEqual(
            [item.state for item in model.items if item.active],
            [JarvisState.THINKING],
        )

    def test_non_operational_state_leaves_all_hud_items_inactive(self):
        model = HudStatusModel.from_state(JarvisState.STANDBY)

        self.assertFalse(any(item.active for item in model.items))

    def test_hud_bounds_stay_in_lower_status_area_at_different_sizes(self):
        self.assertEqual(calculate_hud_bounds((2560, 1400)), (205, 1176, 2355, 1358))
        self.assertEqual(calculate_hud_bounds((1920, 1040)), (154, 874, 1766, 1009))


if __name__ == "__main__":
    unittest.main()

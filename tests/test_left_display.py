import unittest
from pathlib import Path

from ayaka.ui.left_display import (
    AYAKA_OFFICIAL_ASSET,
    fit_contain_size,
    fit_cover_size,
    resolve_ayaka_asset,
)
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


if __name__ == "__main__":
    unittest.main()

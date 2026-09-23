import unittest

from ayaka.commands import AYAKA_NAME_ALIASES, MOMOKA_NAME_ALIASES, CommandRouter, Intent
from ayaka.ui.dashboard import CENTER_CORE_SIZE, CENTER_CARDS, CARD_GRID_COLUMNS, CARD_GRID_ROWS, CARD_REGION


class ProductionAliasTests(unittest.TestCase):
    def test_all_momoka_aliases_route_to_momoka_mode(self):
        router = CommandRouter()
        for alias in MOMOKA_NAME_ALIASES:
            with self.subTest(alias=alias):
                self.assertEqual(router.route(alias), Intent.MOMOKA_MODE)
                self.assertEqual(router.route(f"  {alias}！  "), Intent.MOMOKA_MODE)

    def test_all_ayaka_aliases_route_to_ayaka_mode(self):
        router = CommandRouter()
        for alias in AYAKA_NAME_ALIASES:
            with self.subTest(alias=alias):
                self.assertEqual(router.route(alias), Intent.AYAKA_MODE)
                self.assertEqual(router.route(f"  {alias}？  "), Intent.AYAKA_MODE)

    def test_ambiguous_log_words_are_not_name_aliases(self):
        router = CommandRouter()
        for transcript in ("（笑）", "[音楽]", "はっ", "まんま", "かあ", "ご覧"):
            with self.subTest(transcript=transcript):
                self.assertEqual(router.route(transcript), Intent.UNKNOWN)


class CoreFirstDashboardTests(unittest.TestCase):
    def test_core_is_large_and_cards_are_bottom_two_by_two(self):
        self.assertGreaterEqual(CENTER_CORE_SIZE[0], 700)
        self.assertGreaterEqual(CENTER_CORE_SIZE[1], 700)
        self.assertEqual(CARD_REGION, "bottom")
        self.assertEqual(CARD_GRID_COLUMNS, 2)
        self.assertEqual(CARD_GRID_ROWS, 2)
        self.assertEqual(len(CENTER_CARDS), 4)


if __name__ == "__main__":
    unittest.main()

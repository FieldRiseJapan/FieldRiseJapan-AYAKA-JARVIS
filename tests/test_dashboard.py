import unittest

from ayaka.commands import CommandRouter, Intent
from ayaka.ui.dashboard import CENTER_CARDS, DashboardCard


class NameAliasTests(unittest.TestCase):
    def test_short_names_switch_modes(self):
        router = CommandRouter()
        self.assertEqual(router.route("あや"), Intent.AYAKA_MODE)
        self.assertEqual(router.route("あや！"), Intent.AYAKA_MODE)
        self.assertEqual(router.route("もも"), Intent.MOMOKA_MODE)
        self.assertEqual(router.route("もも！"), Intent.MOMOKA_MODE)


class CenterDashboardTests(unittest.TestCase):
    def test_home_dashboard_has_four_cards_in_requested_order(self):
        self.assertEqual([card.key for card in CENTER_CARDS], ["soundon", "youtube", "tiktok", "instagram"])
        self.assertEqual([card.title for card in CENTER_CARDS], ["SoundOn", "YouTube", "TikTok", "Instagram"])

    def test_unconnected_social_cards_show_data_waiting_placeholders(self):
        cards = {card.key: card for card in CENTER_CARDS}
        self.assertEqual(cards["tiktok"].value, "-- / DATA WAITING")
        self.assertEqual(cards["instagram"].value, "-- / DATA WAITING")
        self.assertIsInstance(cards["tiktok"], DashboardCard)


if __name__ == "__main__":
    unittest.main()

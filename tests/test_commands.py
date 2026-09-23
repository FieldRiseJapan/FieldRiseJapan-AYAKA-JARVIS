import unittest

from ayaka.commands import CommandRouter, Intent
from ayaka.ui.controller import JarvisController
from ayaka.ui.state import DashboardPage, JarvisMode, UiState


class CommandRouterTests(unittest.TestCase):
    def setUp(self):
        self.router = CommandRouter()

    def test_routes_core_commands_and_aliases(self):
        cases = {
            "おはよう": Intent.WAKE,
            "おやすみ": Intent.SLEEP,
            "彩花！": Intent.AYAKA_MODE,
            "桃花": Intent.MOMOKA_MODE,
            "ホーム": Intent.HOME,
            "戻って": Intent.BACK,
            "SoundOn見せて": Intent.SOUNDON,
            "サウンドオン出して": Intent.SOUNDON,
            "GitHub見せて": Intent.GITHUB,
            "ギットハブ出して": Intent.GITHUB,
            "SNSのデータ見せて": Intent.SNS,
        }
        for transcript, expected in cases.items():
            with self.subTest(transcript=transcript):
                self.assertEqual(self.router.route(transcript), expected)

    def test_rejects_unrelated_partial_phrases(self):
        self.assertEqual(self.router.route("今日は桃花色の話"), Intent.UNKNOWN)
        self.assertEqual(self.router.route("音楽を聞きたい"), Intent.UNKNOWN)


class ControllerTests(unittest.TestCase):
    def test_momoka_and_ayaka_mode_switches_update_shared_state(self):
        state = UiState()
        controller = JarvisController(state)
        controller.dispatch(Intent.MOMOKA_MODE)
        self.assertEqual(state.mode, JarvisMode.MOMOKA)
        controller.dispatch(Intent.AYAKA_MODE)
        self.assertEqual(state.mode, JarvisMode.AYAKA)

    def test_navigation_intents_use_existing_history(self):
        state = UiState()
        controller = JarvisController(state)
        controller.dispatch(Intent.SNS)
        controller.dispatch(Intent.SOUNDON)
        controller.dispatch(Intent.BACK)
        self.assertEqual(state.page, DashboardPage.SNS)

    def test_sleep_returns_response_and_requests_close(self):
        state = UiState()
        closed = []
        controller = JarvisController(state, on_close=lambda: closed.append(True))
        response = controller.dispatch(Intent.SLEEP)
        self.assertEqual(response, "おやすみなさい、社長。")
        self.assertEqual(closed, [True])


if __name__ == "__main__":
    unittest.main()

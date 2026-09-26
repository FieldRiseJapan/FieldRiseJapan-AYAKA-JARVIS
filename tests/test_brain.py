import queue
import threading
import unittest

from ayaka.brain.flow import BrainFlow
from ayaka.brain.provider import FallbackProvider
from ayaka.brain.router import BrainRouteKind, BrainRouter
from ayaka.commands import CommandRouter, Intent
from ayaka.ui.state import JarvisMode, JarvisState, UiState
from ayaka.ui.voice_flow import VoiceUiFlow


class BrainRouterTests(unittest.TestCase):
    def test_every_existing_alias_remains_a_command(self):
        brain = BrainRouter()
        for intent, aliases in CommandRouter._aliases.items():
            for alias in aliases:
                with self.subTest(alias=alias):
                    result = brain.route(alias)
                    self.assertEqual(result.kind, BrainRouteKind.COMMAND)
                    self.assertEqual(result.intent, intent)
        for text, intent in (("おやすみ", Intent.SLEEP), ("彩花！", Intent.AYAKA_MODE),
                             ("桃花！", Intent.MOMOKA_MODE)):
            self.assertEqual(brain.route(text).intent, intent)

    def test_unknown_and_partial_phrases_are_conversations(self):
        brain = BrainRouter()
        for text in ("今日は何をしよう？", "今日は桃花色の話", "ホームについて話そう"):
            self.assertEqual(brain.route(text).kind, BrainRouteKind.CONVERSATION)

    def test_fallback_text(self):
        self.assertEqual(FallbackProvider().respond("こんにちは"), "社長、会話機能は現在準備中です。")


class BrainFlowTests(unittest.TestCase):
    def setUp(self):
        self.state = UiState(mode=JarvisMode.AYAKA)
        self.transitions = []
        self.scheduled = []
        self.events = queue.Queue()
        self.commands = []
        self.responses = []
        self.provider = FallbackProvider()
        self.flow = BrainFlow(BrainRouter(), self.provider, lambda: self.state.mode,
                              VoiceUiFlow(self.state), self.schedule, self.commands.append,
                              self.responses.append, self.events)

    def schedule(self, ms, callback):
        self.scheduled.append((ms, callback))

    def advance(self):
        ms, callback = self.scheduled.pop(0)
        self.assertEqual(ms, 550)
        callback()

    def receive_result(self):
        kind, payload = self.events.get(timeout=2)
        self.assertEqual(kind, "brain_response")
        self.flow.complete(*payload)

    def test_command_preserves_two_holds_and_execution(self):
        self.flow.transcript("おやすみ", 550)
        self.assertEqual(self.state.system_state, JarvisState.THINKING)
        self.advance()
        self.assertEqual(self.state.system_state, JarvisState.EXECUTING)
        self.advance()
        self.assertEqual(self.commands, [Intent.SLEEP])

    def test_conversation_skips_execution_and_responds(self):
        self.flow.transcript("今日の調子は？", 550)
        self.advance()
        self.assertEqual(self.state.system_state, JarvisState.THINKING)
        self.receive_result()
        self.assertEqual(self.responses, ["社長、会話機能は現在準備中です。"])

    def test_momoka_unknown_never_calls_provider(self):
        self.state.set_mode(JarvisMode.MOMOKA)
        self.provider.respond = lambda _: self.fail("provider called")
        self.flow.transcript("会話したい", 550)
        self.advance()
        self.assertEqual(self.state.system_state, JarvisState.LISTENING)
        self.assertTrue(self.events.empty())
        self.flow.transcript("彩花！", 550)
        self.advance()
        self.advance()
        self.assertEqual(self.commands, [Intent.AYAKA_MODE])

    def test_none_blank_and_exception_return_to_listening(self):
        for behavior in (lambda _: None, lambda _: "  ", lambda _: 1 / 0):
            with self.subTest(behavior=behavior):
                self.provider.respond = behavior
                self.flow.transcript("雑談", 550)
                self.advance()
                self.receive_result()
                self.assertEqual(self.state.system_state, JarvisState.LISTENING)
        self.assertEqual(self.responses, [])

    def test_stale_result_after_new_transcript_or_mode_change_is_discarded(self):
        self.flow.transcript("古い話", 550)
        self.advance()
        kind, old = self.events.get(timeout=2)
        self.flow.transcript("新しい話", 550)
        self.flow.complete(*old)
        self.assertEqual(self.responses, [])
        self.advance()
        self.state.set_mode(JarvisMode.MOMOKA)
        self.receive_result()
        self.assertEqual(self.responses, [])

    def test_provider_runs_outside_ui_thread_and_invalidation_cancels_pending(self):
        self.provider.respond = lambda _: threading.current_thread().name
        self.flow.transcript("会話", 550)
        self.advance()
        self.receive_result()
        self.assertNotEqual(self.responses, [threading.current_thread().name])
        self.flow.transcript("会話", 550)
        self.flow.invalidate()
        self.advance()
        self.assertEqual(len(self.responses), 1)


if __name__ == "__main__":
    unittest.main()

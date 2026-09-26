import math
import queue
import struct
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

from ayaka.config import AnimationConfig
from ayaka.ui.animation import AnimationController, BlinkPhase, MouthShape
from ayaka.ui.state import JarvisState
from ayaka.ui import voice_sync


class PreparedQueue(queue.Queue):
    def put(self, item):
        super().put(item)
        if item[0] == "speech_prepared":
            item[1][1].set()


class VoiceSyncTests(unittest.TestCase):
    def make_wav(self, path, samples, rate=1000):
        with wave.open(str(path), "wb") as target:
            target.setnchannels(1)
            target.setsampwidth(2)
            target.setframerate(rate)
            target.writeframes(struct.pack("<" + "h" * len(samples), *samples))

    def test_tts_wav_generation_passes_text_as_stdin_and_checks_output(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "speech.wav"

            def fake_run(*args, **kwargs):
                self.assertEqual(kwargs["input"], "社長's voice")
                self.assertTrue(kwargs["check"])
                self.make_wav(output, [0] * 25)

            with patch.object(voice_sync.subprocess, "run", side_effect=fake_run):
                voice_sync.synthesize_wav_windows("社長's voice", output)

    def test_rms_envelope_distinguishes_silence_and_sound(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "speech.wav"
            self.make_wav(output, [0] * 25 + [16000] * 25 + [0] * 25)
            values, duration, threshold = voice_sync.analyze_wav(output)
        self.assertEqual(len(values), 3)
        self.assertAlmostEqual(duration, 0.075)
        self.assertLess(values[0], threshold)
        self.assertGreater(values[1], threshold)
        self.assertLess(values[2], threshold)

    def test_minimum_holds_and_immediate_end(self):
        controller = AnimationController(AnimationConfig(), clock=lambda: 0.0, blink_interval=lambda: 5.0)
        values = (0.0,) * 4 + (0.5,) * 4 + (0.0,) * 4 + (0.5,) * 4
        controller.set_voice_envelope(values, 0.4, 0.1, 1.0)

        def mouth(elapsed):
            return controller.update(JarvisState.SPEAKING, now=1.0 + elapsed).mouth_shape

        self.assertEqual(mouth(-0.01), MouthShape.CLOSED)  # Before playback.
        self.assertEqual(mouth(0.10), MouthShape.OPEN)
        self.assertEqual(mouth(0.125), MouthShape.OPEN)  # Open hold, despite silence.
        self.assertEqual(mouth(0.225), MouthShape.CLOSED)
        self.assertEqual(mouth(0.30), MouthShape.OPEN)
        self.assertEqual(mouth(0.40), MouthShape.CLOSED)  # Ignore hold at end.
        self.assertEqual(controller.update(JarvisState.LISTENING, now=1.41).mouth_shape, MouthShape.CLOSED)

    def test_fallback_keeps_old_interval_and_ignores_blink_and_motion(self):
        controller = AnimationController(AnimationConfig(), clock=lambda: 0.0, blink_interval=lambda: 0.2)
        self.assertEqual(controller.update(JarvisState.SPEAKING, now=0.0).mouth_shape, MouthShape.CLOSED)
        frame = controller.update(JarvisState.SPEAKING, now=0.2)
        self.assertEqual((frame.blink_phase, frame.mouth_shape), (BlinkPhase.HALF, MouthShape.OPEN))
        self.assertTrue(abs(frame.vertical_offset_px) <= 1)
        controller.set_voice_envelope((0.0, 0.5), 0.05, 0.1, 0.2)
        controller.clear_voice_envelope()
        self.assertEqual(controller.update(JarvisState.SPEAKING, now=0.36).mouth_shape, MouthShape.CLOSED)
        controller.reset()  # MOMOKA reset.
        self.assertEqual(controller.update(JarvisState.STANDBY, now=0.36).mouth_shape, MouthShape.CLOSED)
        self.assertEqual(controller.update(JarvisState.STANDBY, now=0.36).vertical_offset_px, 0)

    def test_invalid_envelope_and_wav_fail_closed(self):
        controller = AnimationController(clock=lambda: 0.0)
        with self.assertRaises(ValueError):
            controller.set_voice_envelope((math.nan,), 1.0, 0.1, 0.0)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.wav"
            path.write_bytes(b"broken")
            with self.assertRaises((ValueError, EOFError, wave.Error)):
                voice_sync.analyze_wav(path)

    def test_playback_starts_only_after_preparation_and_completes_closed(self):
        events = PreparedQueue()
        paths = []
        fallback = []

        def synthesize(_text, path):
            paths.append(path)
            self.make_wav(path, [16000] * 50)

        def play(path):
            self.assertEqual(path, paths[0])
            self.assertEqual([item[0] for item in events.queue], ["speech_prepared", "speech_started"])

        with patch.object(voice_sync, "synthesize_wav_windows", side_effect=synthesize), \
             patch.object(voice_sync, "play_wav_windows", side_effect=play):
            voice_sync.speak_with_envelope("hello", 8, events, fallback.append)
        self.assertEqual([item[0] for item in events.queue], ["speech_prepared", "speech_started", "speech_complete"])
        self.assertEqual(fallback, [])
        self.assertFalse(paths[0].exists())

    def test_generation_analysis_and_playback_failures_use_old_speech_and_cleanup(self):
        for failing in ("synthesize_wav_windows", "analyze_wav", "play_wav_windows"):
            with self.subTest(failing=failing):
                events = PreparedQueue()
                fallback = []
                paths = []

                def synthesize(_text, path):
                    paths.append(path)
                patches = {
                    "synthesize_wav_windows": synthesize,
                    "analyze_wav": lambda *_: ((0.2,), 0.025, 0.1),
                    "play_wav_windows": lambda *_: None,
                }

                def fail(*_):
                    raise OSError("simulated failure")

                patches[failing] = fail
                with patch.object(voice_sync, "synthesize_wav_windows", side_effect=patches["synthesize_wav_windows"]), \
                     patch.object(voice_sync, "analyze_wav", side_effect=patches["analyze_wav"]), \
                     patch.object(voice_sync, "play_wav_windows", side_effect=patches["play_wav_windows"]):
                    voice_sync.speak_with_envelope("hello", 7, events, fallback.append)
                observed = list(events.queue)
                self.assertEqual(fallback, ["hello"])
                self.assertIn(("speech_fallback", 7), observed)
                self.assertEqual(observed[-1], ("speech_complete", 7))
                for kind, payload in observed:
                    if kind == "speech_started":
                        self.assertFalse(math.isnan(payload[2]))
                # Temporary files are removed after every exit path.
                self.assertTrue(all(not path.exists() for path in paths))


if __name__ == "__main__":
    unittest.main()

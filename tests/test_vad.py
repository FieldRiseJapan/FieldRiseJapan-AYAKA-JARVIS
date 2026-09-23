import unittest

import numpy as np

from ayaka.config import AppConfig, VadConfig
from ayaka.main import load_config
from ayaka.vad import VadSegmenter


class VadSegmenterTests(unittest.TestCase):
    def test_starts_on_voice_and_keeps_pre_roll(self):
        vad = VadSegmenter(VadConfig(threshold=500, silence_seconds=0.2, pre_roll_seconds=0.1, max_record_seconds=2), sample_rate=1000)
        self.assertIsNone(vad.feed(np.full(50, 100, dtype=np.int16)))
        self.assertIsNone(vad.feed(np.full(50, 1000, dtype=np.int16)))
        segment = vad.feed(np.full(50, 1000, dtype=np.int16))
        self.assertIsNone(segment)
        self.assertEqual(vad.state, "recording")
        self.assertEqual(vad.frames_collected, 150)

    def test_ends_after_configured_silence(self):
        vad = VadSegmenter(VadConfig(threshold=500, silence_seconds=0.2, pre_roll_seconds=0.0, max_record_seconds=2), sample_rate=1000)
        self.assertIsNone(vad.feed(np.full(100, 1000, dtype=np.int16)))
        self.assertIsNone(vad.feed(np.zeros(100, dtype=np.int16)))
        segment = vad.feed(np.zeros(100, dtype=np.int16))
        self.assertIsNotNone(segment)
        self.assertEqual(len(segment), 300)
        self.assertEqual(vad.state, "waiting")

    def test_does_not_emit_when_no_speech_occurs(self):
        vad = VadSegmenter(VadConfig(threshold=500, silence_seconds=0.2, pre_roll_seconds=0.1, max_record_seconds=2), sample_rate=1000)
        for _ in range(10):
            self.assertIsNone(vad.feed(np.zeros(100, dtype=np.int16)))
        self.assertIsNone(vad.flush())

    def test_flushes_at_maximum_record_duration(self):
        vad = VadSegmenter(VadConfig(threshold=500, silence_seconds=0.5, pre_roll_seconds=0.0, max_record_seconds=0.2), sample_rate=1000)
        self.assertIsNone(vad.feed(np.full(100, 1000, dtype=np.int16)))
        segment = vad.feed(np.full(100, 1000, dtype=np.int16))
        self.assertIsNotNone(segment)
        self.assertEqual(len(segment), 200)


class ConfigCompatibilityTests(unittest.TestCase):
    def test_vad_defaults_are_explicit(self):
        config = AppConfig()
        self.assertTrue(config.vad.enabled)
        self.assertEqual(config.vad.threshold, 500)
        self.assertEqual(config.vad.silence_seconds, 0.8)
        self.assertEqual(config.vad.pre_roll_seconds, 0.3)
        self.assertEqual(config.vad.max_record_seconds, 12.0)

    def test_legacy_config_without_vad_uses_defaults(self):
        config = load_config(None)
        self.assertIsInstance(config.vad, VadConfig)
        self.assertTrue(config.vad.enabled)


if __name__ == "__main__":
    unittest.main()

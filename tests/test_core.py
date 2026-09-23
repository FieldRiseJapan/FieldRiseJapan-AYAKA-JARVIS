import unittest

from ayaka.config import AudioConfig, WhisperConfig
from ayaka.devices import choose_input_device
from ayaka.wake import WakeWordDetector


class DeviceSelectionTests(unittest.TestCase):
    def test_prefers_named_wasapi_input_device(self):
        devices = [
            {"name": "Microphone Array", "max_input_channels": 2, "hostapi": "MME"},
            {"name": "Jabra Speak2 40 MS", "max_input_channels": 1, "hostapi": "Windows WASAPI"},
        ]
        selected = choose_input_device(devices, name="Jabra Speak2 40 MS", hostapi="Windows WASAPI")
        self.assertEqual(selected["name"], "Jabra Speak2 40 MS")

    def test_rejects_output_only_device(self):
        devices = [{"name": "Jabra Speak2 40 MS", "max_input_channels": 0, "hostapi": "Windows WASAPI"}]
        with self.assertRaises(ValueError):
            choose_input_device(devices, name="Jabra Speak2 40 MS", hostapi="Windows WASAPI")


class WakeWordTests(unittest.TestCase):
    def test_detects_wake_word_with_punctuation_and_spaces(self):
        detector = WakeWordDetector(["彩花"])
        self.assertTrue(detector.detect("  彩花、おはよう。"))

    def test_does_not_match_unrelated_transcript(self):
        detector = WakeWordDetector(["彩花"])
        self.assertFalse(detector.detect("今日はいい天気ですね"))


class ConfigTests(unittest.TestCase):
    def test_defaults_are_safe_and_explicit(self):
        audio = AudioConfig()
        whisper = WhisperConfig()
        self.assertEqual(audio.sample_rate, 16000)
        self.assertEqual(audio.channels, 1)
        self.assertEqual(whisper.language, "ja")
        self.assertEqual(whisper.chunk_seconds, 5)


if __name__ == "__main__":
    unittest.main()

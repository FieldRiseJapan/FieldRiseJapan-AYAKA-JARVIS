import json
import tempfile
import unittest
from pathlib import Path

from ayaka.config import AnimationConfig, AudioConfig, WhisperConfig
from ayaka.devices import choose_input_device
from ayaka.main import load_config
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

    def test_animation_defaults_enable_subtle_motion(self):
        animation = AnimationConfig()

        self.assertTrue(animation.breathing_enabled)
        self.assertEqual(animation.safe_breathing_amplitude_px, 1)
        self.assertEqual(animation.breathing_period_seconds, 6.0)
        self.assertEqual(animation.frame_interval_ms, 100)

    def test_legacy_config_without_animation_uses_safe_defaults(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.json"
            path.write_text(json.dumps({"wake_words": ["彩花"]}), encoding="utf-8")

            config = load_config(path)

        self.assertTrue(config.animation.breathing_enabled)
        self.assertEqual(config.animation.safe_breathing_amplitude_px, 1)
        self.assertEqual(config.animation.breathing_period_seconds, 6.0)

    def test_example_config_matches_micro_motion_defaults(self):
        example = json.loads((Path(__file__).parents[1] / "config.example.json").read_text(encoding="utf-8"))["animation"]
        defaults = AnimationConfig()
        self.assertEqual(example["breathing_enabled"], defaults.breathing_enabled)
        self.assertEqual(example["breathing_amplitude_px"], defaults.breathing_amplitude_px)
        self.assertEqual(example["breathing_period_seconds"], defaults.breathing_period_seconds)

    def test_animation_config_is_loaded_from_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.json"
            path.write_text(
                json.dumps(
                    {
                        "animation": {
                            "breathing_enabled": True,
                            "breathing_amplitude_px": 2,
                            "breathing_period_seconds": 4.0,
                            "frame_interval_ms": 100,
                        }
                    }
                ),
                encoding="utf-8",
            )

            config = load_config(path)

        self.assertTrue(config.animation.breathing_enabled)
        self.assertEqual(config.animation.safe_breathing_amplitude_px, 2)
        self.assertEqual(config.animation.breathing_period_seconds, 4.0)
        self.assertEqual(config.animation.frame_interval_ms, 100)


if __name__ == "__main__":
    unittest.main()

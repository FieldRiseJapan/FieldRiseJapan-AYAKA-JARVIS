import tempfile
import unittest
import wave
from pathlib import Path

from ayaka.benchmark_stt import BenchmarkResult, benchmark_one, default_model_paths, format_result
from ayaka.config import WhisperConfig


class BenchmarkTests(unittest.TestCase):
    def test_default_model_paths_switch_small_base_tiny_without_en_models(self):
        paths = default_model_paths(Path("vendor/whisper.cpp/ggml-small.bin"))
        self.assertEqual([path.name for path in paths], ["ggml-small.bin", "ggml-base.bin", "ggml-tiny.bin"])
        self.assertTrue(all(".en." not in path.name for path in paths))

    def test_missing_model_returns_clear_nonzero_result(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wav_path = root / "sample.wav"
            _write_silence(wav_path, seconds=1.0)
            result = benchmark_one(
                wav_path,
                WhisperConfig(executable=root / "whisper-cli.exe", model=root / "missing.bin"),
                root,
                model_path=root / "missing.bin",
            )
        self.assertEqual(result.return_code, 2)
        self.assertIn("not found", result.text.lower())

    def test_result_reports_time_rtf_and_exit_code(self):
        result = BenchmarkResult("small", Path("small.bin"), 1.25, "おはよう", 0, 5.0)
        rendered = format_result(result)
        self.assertIn("MODEL: small", rendered)
        self.assertIn("TIME: 1.25 sec", rendered)
        self.assertIn("TEXT: おはよう", rendered)
        self.assertIn("EXIT_CODE: 0", rendered)
        self.assertIn("RTF: 0.250", rendered)


def _write_silence(path: Path, seconds: float):
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(b"\x00\x00" * int(16000 * seconds))


if __name__ == "__main__":
    unittest.main()

from dataclasses import dataclass, replace
import argparse
from pathlib import Path
import time
import wave

from .config import WhisperConfig
from .stt import WhisperCppSTT


@dataclass(frozen=True)
class BenchmarkResult:
    label: str
    model_path: Path
    elapsed_seconds: float
    text: str
    return_code: int
    audio_seconds: float

    @property
    def rtf(self) -> float | None:
        if self.audio_seconds <= 0:
            return None
        return self.elapsed_seconds / self.audio_seconds


def default_model_paths(configured_model: Path) -> list[Path]:
    """Return multilingual sibling candidates without selecting .en models."""
    names = ("ggml-small.bin", "ggml-base.bin", "ggml-tiny.bin")
    return [configured_model.with_name(name) for name in names]


def model_label(model_path: Path) -> str:
    stem = model_path.stem
    return stem.removeprefix("ggml-")


def wav_duration(wav_path: Path) -> float:
    with wave.open(str(wav_path), "rb") as wav:
        frames = wav.getnframes()
        rate = wav.getframerate()
    return frames / rate if rate else 0.0


def benchmark_one(
    wav_path: Path,
    whisper_config: WhisperConfig,
    project_root: Path,
    *,
    model_path: Path | None = None,
) -> BenchmarkResult:
    selected_model = model_path or whisper_config.model
    config = replace(whisper_config, model=selected_model)
    label = model_label(selected_model)
    started = time.perf_counter()
    try:
        text = WhisperCppSTT(config, project_root).transcribe(wav_path)
        return_code = 0
    except FileNotFoundError as exc:
        text = f"ERROR: {exc}"
        return_code = 2
    except (RuntimeError, OSError) as exc:
        text = f"ERROR: {exc}"
        return_code = 1
    elapsed = time.perf_counter() - started
    return BenchmarkResult(label, selected_model, elapsed, text, return_code, wav_duration(wav_path))


def format_result(result: BenchmarkResult) -> str:
    rtf = "N/A" if result.rtf is None else f"{result.rtf:.3f}"
    return "\n".join(
        [
            f"MODEL: {result.label}",
            f"PATH: {result.model_path}",
            f"TIME: {result.elapsed_seconds:.2f} sec",
            f"AUDIO: {result.audio_seconds:.2f} sec",
            f"RTF: {rtf}",
            f"TEXT: {result.text}",
            f"EXIT_CODE: {result.return_code}",
        ]
    )


def parse_model_paths(value: str | None, configured_model: Path) -> list[Path]:
    if not value:
        return default_model_paths(configured_model)
    paths = [Path(item.strip()) for item in value.split(",") if item.strip()]
    if not paths:
        raise ValueError("--models must contain at least one model path")
    if any(path.name.endswith(".en.bin") for path in paths):
        raise ValueError("English-only .en models are not supported; use multilingual models")
    return paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Benchmark whisper.cpp multilingual STT models on one WAV")
    parser.add_argument("wav", type=Path, help="WAV recorded on the Windows/Jabra machine")
    parser.add_argument("--config", type=Path, default=Path("config.json"))
    parser.add_argument("--models", help="Comma-separated multilingual model paths; default: small,base,tiny siblings")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    return parser


def main(args: argparse.Namespace | None = None) -> int:
    from .main import load_config

    parsed = args or build_parser().parse_args()
    config = load_config(parsed.config)
    if not parsed.wav.exists():
        print(f"ERROR: WAV file not found: {parsed.wav}")
        return 2
    try:
        models = parse_model_paths(parsed.models, config.whisper.model)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 2
    results = []
    for model in models:
        result = benchmark_one(parsed.wav, config.whisper, parsed.project_root, model_path=model)
        results.append(result)
        print(format_result(result))
        print()
    return 0 if all(result.return_code == 0 for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())

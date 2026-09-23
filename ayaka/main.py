import argparse
import json
from pathlib import Path
import subprocess

from .config import AppConfig, AudioConfig, VadConfig, WhisperConfig
from .recorder import record_wav
from .stt import WhisperCppSTT
from .wake import WakeWordDetector


def load_config(path: Path | None) -> AppConfig:
    if path is None or not path.exists():
        return AppConfig()
    raw = json.loads(path.read_text(encoding="utf-8"))
    audio = AudioConfig(**raw.get("audio", {}))
    vad = VadConfig(**raw.get("vad", {}))
    whisper_data = raw.get("whisper", {})
    if "executable" in whisper_data:
        whisper_data["executable"] = Path(whisper_data["executable"])
    if "model" in whisper_data:
        whisper_data["model"] = Path(whisper_data["model"])
    whisper = WhisperConfig(**whisper_data)
    return AppConfig(
        audio=audio,
        vad=vad,
        whisper=whisper,
        wake_words=tuple(raw.get("wake_words", ["彩花"])),
        reply_text=raw.get("reply_text", "はい、社長。"),
    )


def speak_windows(text: str) -> None:
    escaped = text.replace("'", "''")
    script = "Add-Type -AssemblyName System.Speech; $s=New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.Speak('" + escaped + "')"
    subprocess.run(["powershell", "-NoProfile", "-Command", script], check=False)


def run(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    stt = WhisperCppSTT(config.whisper, Path.cwd())
    detector = WakeWordDetector(config.wake_words)
    if args.wav:
        transcript = stt.transcribe(args.wav)
        print(f"📝 認識結果: {transcript}")
        if detector.detect(transcript):
            print(f"🔔 ウェイクワード検出: {', '.join(config.wake_words)}")
            if args.tts:
                print(f"🗣️ AYAKA: {config.reply_text}")
                speak_windows(config.reply_text)
        return 0

    output = Path(args.work_dir) / "ayaka_latest.wav"
    print("AYAKA JARVIS v0.1", flush=True)
    print(f"入力デバイス: {config.audio.device_name} / {config.audio.hostapi_name}", flush=True)
    while True:
        recorded = record_wav(output, config.audio, config.vad)
        if recorded is None:
            continue
        print("🧠 音声認識中...", flush=True)
        transcript = stt.transcribe(output)
        if transcript:
            print(f"📝 認識結果: {transcript}", flush=True)
        if detector.detect(transcript):
            print(f"🔔 ウェイクワード検出: {', '.join(config.wake_words)}", flush=True)
            if args.tts:
                print(f"🗣️ AYAKA: {config.reply_text}", flush=True)
                speak_windows(config.reply_text)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AYAKA JARVIS voice input v0.1")
    parser.add_argument("--config", type=Path, default=Path("config.json"))
    parser.add_argument("--wav", type=Path, help="Transcribe an existing WAV file once")
    parser.add_argument("--work-dir", type=Path, default=Path("runtime"))
    parser.add_argument("--tts", action="store_true", help="Speak the wake response using Windows PowerShell")
    return parser


if __name__ == "__main__":
    raise SystemExit(run(build_parser().parse_args()))

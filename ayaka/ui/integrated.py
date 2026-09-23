from pathlib import Path
import argparse
import queue
import threading

from ..commands import CommandRouter
from ..config import AppConfig
from ..main import load_config, speak_windows
from ..recorder import record_wav
from ..stt import WhisperCppSTT
from .controller import JarvisController
from .monitors import discover_layout
from .voice_flow import VoiceUiFlow


STATE_HOLD_MS = 550


class VoiceWorker:
    def __init__(self, config: AppConfig, work_dir: Path, output_queue: queue.Queue):
        self.config = config
        self.work_dir = work_dir
        self.output_queue = output_queue
        self.stop_event = threading.Event()
        self.thread: threading.Thread | None = None

    def start(self):
        self.thread = threading.Thread(target=self._run, name="ayaka-voice-worker", daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()

    def _run(self):
        output = self.work_dir / "ayaka_latest.wav"
        stt = WhisperCppSTT(self.config.whisper, Path.cwd())
        while not self.stop_event.is_set():
            try:
                recorded = record_wav(output, self.config.audio, self.config.vad)
                if recorded is None:
                    continue
                transcript = stt.transcribe(output)
                if transcript:
                    self.output_queue.put(("transcript", transcript))
            except Exception as exc:  # keep the UI alive and surface worker failures
                self.output_queue.put(("error", str(exc)))
                return


def run(config_path: Path, work_dir: Path):
    from .app import JarvisUiApp

    config = load_config(config_path)
    events: queue.Queue = queue.Queue()
    router = CommandRouter()
    worker: VoiceWorker | None = None
    app: JarvisUiApp | None = None

    def close_ui():
        if worker:
            worker.stop()
        if app and app.root:
            app.root.after(700, app.close)

    controller = JarvisController(on_close=close_ui)
    voice_flow = VoiceUiFlow(controller.state)

    def speak_and_signal(response: str):
        try:
            speak_windows(response)
        finally:
            events.put(("speech_complete", None))

    def dispatch_transcript(transcript: str):
        if not app or not app.root:
            return
        intent = router.route(transcript)
        response = controller.dispatch(intent)
        if response:
            voice_flow.begin_speaking()
            threading.Thread(target=speak_and_signal, args=(response,), daemon=True).start()
        else:
            voice_flow.speech_completed()

    def begin_execution(transcript: str):
        if not app or not app.root:
            return
        voice_flow.begin_execution()
        app.root.after(STATE_HOLD_MS, lambda: dispatch_transcript(transcript))

    def poll_events():
        if not app or not app.root:
            return
        try:
            while True:
                kind, payload = events.get_nowait()
                if kind == "transcript":
                    voice_flow.transcript_received()
                    app.root.after(STATE_HOLD_MS, lambda transcript=payload: begin_execution(transcript))
                elif kind == "speech_complete":
                    voice_flow.speech_completed()
                elif kind == "error":
                    print(f"VOICE WORKER ERROR: {payload}", flush=True)
        except queue.Empty:
            pass
        app.root.after(100, poll_events)

    def on_ready(current_app):
        nonlocal app, worker
        app = current_app
        worker = VoiceWorker(config, work_dir, events)
        voice_flow.begin_listening()
        worker.start()
        poll_events()

    app = JarvisUiApp(layout=discover_layout(), state=controller.state, on_ready=on_ready)
    try:
        app.run()
    finally:
        if worker:
            worker.stop()


def build_parser():
    parser = argparse.ArgumentParser(description="AYAKA JARVIS v0.2 integrated voice and UI launcher")
    parser.add_argument("--config", type=Path, default=Path("config.json"))
    parser.add_argument("--work-dir", type=Path, default=Path("runtime"))
    return parser


def main(args=None):
    parsed = args or build_parser().parse_args()
    run(parsed.config, parsed.work_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

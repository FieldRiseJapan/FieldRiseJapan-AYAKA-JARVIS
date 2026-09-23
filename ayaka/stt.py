from pathlib import Path
import subprocess
import tempfile


class WhisperCppSTT:
    def __init__(self, config, project_root: Path | None = None):
        root = project_root or Path.cwd()
        self.executable = self._resolve(root, config.executable)
        self.model = self._resolve(root, config.model)
        self.language = config.language
        self.temperature = config.temperature

    @staticmethod
    def _resolve(root: Path, path: Path) -> Path:
        return path if path.is_absolute() else root / path

    def transcribe(self, wav_path: Path) -> str:
        if not self.executable.exists():
            raise FileNotFoundError(f"whisper executable not found: {self.executable}")
        if not self.model.exists():
            raise FileNotFoundError(f"whisper model not found: {self.model}")
        with tempfile.TemporaryDirectory(prefix="ayaka-whisper-") as directory:
            output_base = Path(directory) / "transcript"
            command = [
                str(self.executable), "-m", str(self.model), "-f", str(wav_path),
                "-l", self.language, "-otxt", "-of", str(output_base),
                "-nt", "-np", "-t", "0", "--temperature", str(self.temperature),
            ]
            completed = subprocess.run(command, capture_output=True, text=True, check=False)
            if completed.returncode != 0:
                raise RuntimeError(
                    f"whisper.cpp failed with exit code {completed.returncode}: "
                    f"{completed.stderr.strip()}"
                )
            text_file = output_base.with_suffix(".txt")
            if text_file.exists():
                return text_file.read_text(encoding="utf-8").strip()
            return completed.stdout.strip()

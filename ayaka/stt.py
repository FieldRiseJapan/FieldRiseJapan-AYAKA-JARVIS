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
            raise FileNotFoundError(
                f"whisper executable not found: {self.executable}"
            )

        if not self.model.exists():
            raise FileNotFoundError(
                f"whisper model not found: {self.model}"
            )

        with tempfile.TemporaryDirectory(prefix="ayaka-whisper-") as directory:
            output_base = Path(directory) / "transcript"

            command = [
                str(self.executable),
                "-m", str(self.model),
                "-f", str(wav_path),
                "-l", self.language,
                "-otxt",
                "-of", str(output_base),
                "-nt",
                "-np",
                "--temperature", str(self.temperature),
            ]

            print("WHISPER COMMAND:", command, flush=True)

            completed = subprocess.run(
                command,
                check=False,
            )

            if completed.returncode != 0:
                raise RuntimeError(
                    f"whisper.cpp failed with exit code "
                    f"{completed.returncode}"
                )

            text_file = output_base.with_suffix(".txt")

            if not text_file.exists():
                raise RuntimeError(
                    f"whisper output file was not created: {text_file}"
                )

            return text_file.read_text(
                encoding="utf-8"
            ).strip()
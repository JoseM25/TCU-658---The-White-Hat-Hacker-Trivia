"""
Minimal Piper TTS helper used by the project.

This module offers a light wrapper around the Piper command line interface so
code can synthesize and play audio without duplicating subprocess logic or
platform-specific audio handling in the UI layer.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:
    import winsound

    _WINSOUND_AVAILABLE = True
except ImportError:
    winsound = None
    _WINSOUND_AVAILABLE = False


class PiperVoiceError(RuntimeError):
    """Raised when Piper synthesis or playback cannot be completed."""


@dataclass(frozen=True)
class PiperModel:
    model_path: Path
    config_path: Optional[Path] = None

    def __post_init__(self) -> None:
        if not self.model_path.exists():
            raise PiperVoiceError(f"Piper model not found: {self.model_path}")
        if self.config_path and not self.config_path.exists():
            raise PiperVoiceError(f"Piper config not found: {self.config_path}")


class PiperVoice:
    """
    Simple Piper front-end that synthesizes text to wav files and can play them.

    Parameters
    ----------
    model_path:
        Path to the ONNX model file.
    config_path:
        Path to the JSON config file for the model.
    executable:
        Optional override for the Piper executable path. Defaults to the first
        `piper` found on PATH.
    auto_cleanup:
        When True, temporary audio artifacts are deleted automatically when a
        new synthesis is requested or upon calling `stop()`.
    """

    def __init__(
        self,
        model_path: Path | str,
        config_path: Path | str | None = None,
        *,
        executable: Path | str | None = None,
        auto_cleanup: bool = True,
    ) -> None:
        self.model = PiperModel(
            model_path=Path(model_path),
            config_path=Path(config_path) if config_path else None,
        )
        self._auto_cleanup = auto_cleanup
        self._executable = Path(executable) if executable else shutil.which("piper")
        if not self._executable:
            raise PiperVoiceError("Piper executable not found on PATH.")

        self._current_audio: Optional[Path] = None

    def synthesize_to_file(
        self,
        text: str,
        *,
        output_path: Path | str | None = None,
    ) -> Path:
        """
        Generate speech audio for `text` and return the wav file path.

        When `output_path` is not provided, a temporary file is created.
        """
        cleaned_text = (text or "").strip()
        if not cleaned_text:
            raise PiperVoiceError("Cannot synthesize empty text.")

        if output_path:
            audio_path = Path(output_path)
            audio_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            file_descriptor, temp_path = tempfile.mkstemp(suffix=".wav")
            os.close(file_descriptor)
            audio_path = Path(temp_path)

        command = [
            str(self._executable),
            "--model",
            str(self.model.model_path),
            "--output_file",
            str(audio_path),
        ]

        if self.model.config_path:
            command.extend(["--config", str(self.model.config_path)])

        input_text = cleaned_text if cleaned_text.endswith("\n") else f"{cleaned_text}\n"

        result = subprocess.run(
            command,
            input=input_text,
            text=True,
            capture_output=True,
            check=False,
        )

        if result.returncode != 0:
            error_message = result.stderr.strip() if result.stderr else "Unknown Piper error."
            raise PiperVoiceError(error_message)

        self._register_audio_path(audio_path)
        return audio_path

    def speak(self, text: str) -> Path:
        """
        Synthesize `text` and play the resulting audio asynchronously.

        Returns the path to the generated wav file.
        """
        audio_path = self.synthesize_to_file(text)
        self.play_file(audio_path)
        return audio_path

    def play_file(self, audio_path: Path | str) -> None:
        """Play an existing wav file asynchronously."""
        path_obj = Path(audio_path)
        if not path_obj.exists():
            raise PiperVoiceError(f"Audio file does not exist: {path_obj}")

        if _WINSOUND_AVAILABLE:
            winsound.PlaySound(
                str(path_obj),
                winsound.SND_FILENAME | winsound.SND_ASYNC,
            )
        else:
            raise PiperVoiceError(
                "Audio playback is not supported on this platform without winsound."
            )

    def stop(self) -> None:
        """
        Stop any in-progress playback and remove temporary audio files if enabled.
        """
        if _WINSOUND_AVAILABLE:
            winsound.PlaySound(None, winsound.SND_PURGE)
        self._cleanup_current_audio()

    def _register_audio_path(self, audio_path: Path) -> None:
        if self._auto_cleanup:
            self._cleanup_current_audio()
            self._current_audio = audio_path

    def _cleanup_current_audio(self) -> None:
        if self._current_audio and self._current_audio.exists():
            try:
                self._current_audio.unlink()
            except OSError:
                pass
        self._current_audio = None

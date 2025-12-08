import io
import logging
import threading
import wave
import winsound
from pathlib import Path
from tempfile import NamedTemporaryFile

from piper.voice import PiperVoice

# Suppress Piper warnings
logging.getLogger("piper.voice").setLevel(logging.ERROR)


class TTSService:

    def __init__(self, model_dir, model_name="en_US-ryan-high.onnx"):
        self.model_path = Path(model_dir) / model_name
        self.config_path = Path(model_dir) / f"{model_name}.json"
        self._voice = None
        self._speaking_thread = None
        self._load_lock = threading.Lock()
        self._load_error = None

    def preload(self):
        """Load the voice model once so subsequent calls are fast."""
        self._ensure_voice_loaded()

    def speak(self, text):
        if not text or not text.strip():
            return

        if not self._ensure_voice_loaded():
            return

        self.stop()
        self._speaking_thread = threading.Thread(
            target=self.speak_worker, args=(text,), daemon=True
        )
        self._speaking_thread.start()

    def speak_worker(self, text):
        try:
            if not self._voice:
                return

            # Synthesize audio to WAV in memory
            buffer = io.BytesIO()
            wav_file = wave.open(buffer, "wb")
            wav_configured = False

            for chunk in self._voice.synthesize(text):
                if not wav_configured:
                    wav_file.setnchannels(chunk.sample_channels)
                    wav_file.setsampwidth(chunk.sample_width)
                    wav_file.setframerate(chunk.sample_rate)
                    wav_configured = True
                wav_file.writeframes(chunk.audio_int16_bytes)

            wav_file.close()

            # Play audio from temporary file
            with NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(buffer.getvalue())
                tmp.flush()
                winsound.PlaySound(tmp.name, winsound.SND_FILENAME | winsound.SND_ASYNC)

        except Exception:  # pylint: disable=broad-except
            # Silently fail - TTS is non-critical
            pass

    def stop(self):
        try:
            winsound.PlaySound(None, winsound.SND_PURGE)
        except Exception:  # pylint: disable=broad-except
            pass

    def _ensure_voice_loaded(self):
        """Load the Piper voice once, caching the result."""
        if self._voice or self._load_error:
            return self._voice

        with self._load_lock:
            if self._voice or self._load_error:
                return self._voice
            try:
                self._voice = PiperVoice.load(
                    str(self.model_path), str(self.config_path)
                )
            except Exception as error:  # pylint: disable=broad-except
                self._load_error = error
                print(f"Warning: Unable to load TTS voice: {error}")
        return self._voice

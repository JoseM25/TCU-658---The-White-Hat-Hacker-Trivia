import io
import logging
import threading
import wave
import winsound
from contextlib import suppress
from pathlib import Path
from tempfile import NamedTemporaryFile

from piper.voice import PiperVoice

# Suppress Piper phoneme warnings
logging.getLogger("piper.voice").setLevel(logging.ERROR)


class TTSService:

    def __init__(self, model_dir, model_name="en_US-ryan-high.onnx"):
        self.model_path = Path(model_dir) / model_name
        self.config_path = Path(model_dir) / f"{model_name}.json"
        self._voice = None
        self._speaking_thread = None

    def speak(self, text):
        if not text or not text.strip():
            return

        # Stop any current speech
        self.stop()

        # Start new speech in background thread
        self._speaking_thread = threading.Thread(
            target=self._speak_worker, args=(text,), daemon=True
        )
        self._speaking_thread.start()

    def _speak_worker(self, text):
        # Lazy-load voice model on first use
        if not self._voice:
            with suppress(Exception):
                self._voice = PiperVoice.load(
                    str(self.model_path), str(self.config_path)
                )
            if not self._voice:
                return

        # Synthesize audio to WAV format in memory
        with suppress(Exception):
            buffer = io.BytesIO()
            with wave.open(buffer, "wb") as wav:  # type: ignore
                for i, chunk in enumerate(self._voice.synthesize(text)):
                    if i == 0:  # Configure WAV on first chunk
                        wav.setnchannels(chunk.sample_channels)
                        wav.setsampwidth(chunk.sample_width)
                        wav.setframerate(chunk.sample_rate)
                    wav.writeframes(chunk.audio_int16_bytes)

            # Play audio from temporary file
            with NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(buffer.getvalue())
                tmp.flush()
                winsound.PlaySound(tmp.name, winsound.SND_FILENAME | winsound.SND_ASYNC)

    def stop(self):
        with suppress(Exception):
            winsound.PlaySound(None, winsound.SND_PURGE)

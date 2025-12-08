import io
import logging
import threading
import wave
import winsound
from pathlib import Path
from tempfile import NamedTemporaryFile

from piper.voice import PiperVoice

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

            with NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(buffer.getvalue())
                tmp.flush()
                winsound.PlaySound(tmp.name, winsound.SND_FILENAME | winsound.SND_ASYNC)

        except Exception:
            pass

    def stop(self):
        try:
            winsound.PlaySound(None, winsound.SND_PURGE)
        except Exception:
            pass

    def _ensure_voice_loaded(self):
        if self._voice or self._load_error:
            return self._voice

        with self._load_lock:
            if self._voice or self._load_error:
                return self._voice
            try:
                self._voice = PiperVoice.load(
                    str(self.model_path), str(self.config_path)
                )
            except Exception as error:
                self._load_error = error
                print(f"Warning: Unable to load TTS voice: {error}")
        return self._voice

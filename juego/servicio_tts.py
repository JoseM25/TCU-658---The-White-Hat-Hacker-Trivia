import io
import logging
import os
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
        self._temp_files = []
        self._temp_lock = threading.Lock()

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
                tmp_path = tmp.name
                tmp.write(buffer.getvalue())
                tmp.flush()

            with self._temp_lock:
                self._temp_files.append(tmp_path)

            winsound.PlaySound(tmp_path, winsound.SND_FILENAME | winsound.SND_ASYNC)

            # Schedule cleanup of old temp files after a delay
            threading.Timer(5.0, self._cleanup_old_temp_files).start()

        except (OSError, wave.Error, RuntimeError, ValueError) as error:
            logging.exception("Failed to synthesize speech: %s", error)

    def _cleanup_old_temp_files(self):
        """Clean up temp files that are no longer playing."""
        with self._temp_lock:
            # Keep only the most recent file (might still be playing)
            files_to_remove = self._temp_files[:-1]
            self._temp_files = self._temp_files[-1:] if self._temp_files else []

        for tmp_path in files_to_remove:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    def stop(self):
        try:
            winsound.PlaySound(None, winsound.SND_PURGE)
        except (RuntimeError, OSError):
            # Ignore playback errors when trying to stop audio.
            pass

        # Clean up all temp files when stopping
        with self._temp_lock:
            for tmp_path in self._temp_files:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
            self._temp_files.clear()

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
            except (FileNotFoundError, OSError, RuntimeError, ValueError) as error:
                self._load_error = error
                print(f"Warning: Unable to load TTS voice: {error}")
        return self._voice

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
        self.voice = None
        self.speaking_thread = None
        self.load_lock = threading.Lock()
        self.load_error = None
        self.temp_files = []
        self.temp_lock = threading.Lock()

    def preload(self):
        self.ensure_voice_loaded()

    def speak(self, text):
        if not text or not text.strip():
            return

        if not self.ensure_voice_loaded():
            return

        self.stop()
        self.speaking_thread = threading.Thread(
            target=self.speak_worker, args=(text,), daemon=True
        )
        self.speaking_thread.start()

    def speak_worker(self, text):
        try:
            if not self.voice:
                return

            buffer = io.BytesIO()
            wav_file = wave.open(buffer, "wb")
            wav_configured = False

            for chunk in self.voice.synthesize(text):
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

            with self.temp_lock:
                self.temp_files.append(tmp_path)

            winsound.PlaySound(tmp_path, winsound.SND_FILENAME | winsound.SND_ASYNC)

            # Programar limpieza de archivos temporales viejos después de un retraso
            threading.Timer(5.0, self.cleanup_old_temp_files).start()

        except (OSError, wave.Error, RuntimeError, ValueError) as error:
            logging.exception("Failed to synthesize speech: %s", error)

    def cleanup_old_temp_files(self):
        with self.temp_lock:
            # Mantener solo el archivo más reciente (podría estar reproduciéndose)
            files_to_remove = self.temp_files[:-1]
            self.temp_files = self.temp_files[-1:] if self.temp_files else []

        for tmp_path in files_to_remove:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    def stop(self):
        try:
            winsound.PlaySound(None, winsound.SND_PURGE)
        except (RuntimeError, OSError):
            # Ignorar errores de reproducción al detener audio.
            pass

        # Limpiar todos los archivos temporales al detener
        with self.temp_lock:
            for tmp_path in self.temp_files:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
            self.temp_files.clear()

    def shutdown(self):
        """Clean up all resources. Call on application exit."""
        self.stop()
        self.voice = None

    def ensure_voice_loaded(self):
        if self.voice or self.load_error:
            return self.voice

        with self.load_lock:
            if self.voice or self.load_error:
                return self.voice
            try:
                self.voice = PiperVoice.load(
                    str(self.model_path), str(self.config_path)
                )
            except (FileNotFoundError, OSError, RuntimeError, ValueError) as error:
                self.load_error = error
                print(f"Warning: Unable to load TTS voice: {error}")
        return self.voice

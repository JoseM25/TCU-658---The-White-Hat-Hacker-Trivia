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
        self.speaking_cancelled = threading.Event()
        self.load_lock = threading.Lock()
        self.load_error = None
        self.temp_files = []
        self.temp_lock = threading.Lock()
        self.cleanup_timer = None
        self.cleanup_timer_lock = threading.Lock()
        self.audiocache = {}
        self.audiocacheorder = []
        self.audiocachemax = 20
        self.cachelock = threading.Lock()

    def preload(self):
        self.ensure_voice_loaded()

    def speak(self, text):
        if not text or not text.strip():
            return
        text = text.strip()

        cachedpath = None
        with self.cachelock:
            cachedpath = self.audiocache.get(text)

        if cachedpath and os.path.exists(cachedpath):
            self.stop()
            self.speaking_cancelled.clear()
            winsound.PlaySound(cachedpath, winsound.SND_FILENAME | winsound.SND_ASYNC)
            self.schedule_cleanup_timer()
            return
        if cachedpath and not os.path.exists(cachedpath):
            with self.cachelock:
                if self.audiocache.get(text) == cachedpath:
                    self.audiocache.pop(text, None)

        if not self.ensure_voice_loaded():
            return

        self.stop()
        self.speaking_cancelled.clear()
        self.speaking_thread = threading.Thread(
            target=self.speak_worker, args=(text,), daemon=True
        )
        self.speaking_thread.start()

    def speak_worker(self, text):
        try:
            if not self.voice:
                return

            # Check if cancelled before starting
            if self.speaking_cancelled.is_set():
                return

            buffer = io.BytesIO()
            wav_file = wave.open(buffer, "wb")
            wav_configured = False

            for chunk in self.voice.synthesize(text):
                # Check cancellation during synthesis
                if self.speaking_cancelled.is_set():
                    wav_file.close()
                    return
                if not wav_configured:
                    wav_file.setnchannels(chunk.sample_channels)
                    wav_file.setsampwidth(chunk.sample_width)
                    wav_file.setframerate(chunk.sample_rate)
                    wav_configured = True
                wav_file.writeframes(chunk.audio_int16_bytes)

            wav_file.close()

            # Check if cancelled after synthesis
            if self.speaking_cancelled.is_set():
                return

            with NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name
                tmp.write(buffer.getvalue())
                tmp.flush()

            with self.temp_lock:
                self.temp_files.append(tmp_path)

            with self.cachelock:
                self.audiocache[text] = tmp_path
                self.audiocacheorder.append(text)
                while len(self.audiocacheorder) > self.audiocachemax:
                    viejo = self.audiocacheorder.pop(0)
                    pathviejo = self.audiocache.pop(viejo, None)
                    if pathviejo and pathviejo != tmp_path:
                        try:
                            os.unlink(pathviejo)
                        except OSError:
                            pass

            winsound.PlaySound(tmp_path, winsound.SND_FILENAME | winsound.SND_ASYNC)

            # Schedule cleanup with deduplication - cancel existing timer first
            self.schedule_cleanup_timer()

        except (OSError, wave.Error, RuntimeError, ValueError) as error:
            logging.exception("Failed to synthesize speech: %s", error)

    def schedule_cleanup_timer(self):
        """Schedule cleanup with deduplication - only one timer runs at a time."""
        with self.cleanup_timer_lock:
            # Cancel existing cleanup timer if any
            if self.cleanup_timer is not None:
                self.cleanup_timer.cancel()
            # Schedule new cleanup timer
            self.cleanup_timer = threading.Timer(5.0, self.cleanup_old_temp_files)
            self.cleanup_timer.daemon = True
            self.cleanup_timer.start()

    def cleanup_old_temp_files(self):
        with self.cleanup_timer_lock:
            self.cleanup_timer = None

        with self.cachelock:
            cachepaths = set(self.audiocache.values())

        with self.temp_lock:
            # Mantener los últimos 2 archivos por seguridad en lugar de 1
            # Esto reduce drásticamente el riesgo de borrar el archivo en reproducción
            if len(self.temp_files) > 2:
                files_to_remove = self.temp_files[:-2]
                self.temp_files = self.temp_files[-2:]
            else:
                files_to_remove = []

        for tmp_path in files_to_remove:
            if tmp_path in cachepaths:
                continue
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    def stop(self):
        # Signal any running thread to stop
        self.speaking_cancelled.set()

        try:
            winsound.PlaySound(None, winsound.SND_PURGE)
        except (RuntimeError, OSError):
            # Ignorar errores de reproducción al detener audio.
            pass

        # Cancel any pending cleanup timer
        with self.cleanup_timer_lock:
            if self.cleanup_timer is not None:
                self.cleanup_timer.cancel()
                self.cleanup_timer = None

        # Limpiar todos los archivos temporales al detener
        with self.temp_lock:
            with self.cachelock:
                cachepaths = set(self.audiocache.values())
            restantes = []
            for tmp_path in self.temp_files:
                if tmp_path in cachepaths:
                    restantes.append(tmp_path)
                    continue
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
            self.temp_files = restantes

    def shutdown(self):
        """Clean up all resources. Call on application exit."""
        self.stop()
        # Wait for speaking thread to finish if running (with timeout)
        if self.speaking_thread is not None and self.speaking_thread.is_alive():
            self.speaking_thread.join(timeout=1.0)
        self.speaking_thread = None
        with self.cachelock:
            cachepaths = list(self.audiocache.values())
            self.audiocache.clear()
            self.audiocacheorder.clear()
        for path in cachepaths:
            try:
                os.unlink(path)
            except OSError:
                pass
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

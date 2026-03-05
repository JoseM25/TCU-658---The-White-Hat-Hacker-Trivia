import io
import logging
import threading
import wave
from pathlib import Path

from piper.voice import PiperVoice

try:
    import pygame
except ImportError:
    pygame = None

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
        self.load_retries = 0
        self.audiocache = {}
        self.audiocacheorder = []
        self.audiocachemax = 20
        self.cachelock = threading.Lock()
        self.speakgen = 0

        # Dedicated channel for TTS (channel 2, reserved by SFXService)
        self.tts_channel = None
        self.playback_lock = threading.Lock()

    def play_sound(self, sound):
        if pygame is None or sound is None:
            return

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

            if self.tts_channel is None:
                self.tts_channel = pygame.mixer.Channel(2)

            with self.playback_lock:
                self.tts_channel.stop()
                self.tts_channel.play(sound)

        except (pygame.error, OSError, RuntimeError) as e:
            logging.error("TTS Playback failed: %s", e)

    def preload(self):
        self.ensure_voice_loaded()

    def speak(self, text):
        if not text or not text.strip():
            return
        text = text.strip()

        cached_sound = None
        with self.cachelock:
            cached_sound = self.audiocache.get(text)

        if cached_sound:
            self.stop()
            self.speakgen += 1
            self.speaking_cancelled.clear()
            self.play_sound(cached_sound)
            return

        if not self.ensure_voice_loaded():
            return

        self.stop()
        self.speakgen += 1
        self.speaking_cancelled.clear()
        gen = self.speakgen
        self.speaking_thread = threading.Thread(
            target=self.speak_worker, args=(text, gen), daemon=True
        )
        self.speaking_thread.start()

    def speak_worker(self, text, gen):
        wav_file = None
        try:
            if not self.voice:
                return

            if self.speaking_cancelled.is_set() or gen != self.speakgen:
                return

            buffer = io.BytesIO()

            for chunk in self.voice.synthesize(text):
                if self.speaking_cancelled.is_set() or gen != self.speakgen:
                    return
                if wav_file is None:
                    wav_file = wave.open(buffer, "wb")
                    wav_file.setnchannels(chunk.sample_channels)
                    wav_file.setsampwidth(chunk.sample_width)
                    wav_file.setframerate(chunk.sample_rate)
                wav_file.writeframes(chunk.audio_int16_bytes)

            if wav_file is None:
                return

            wav_file.close()
            wav_file = None

            if self.speaking_cancelled.is_set() or gen != self.speakgen:
                return

            # Crear sonido directamente desde el búfer de memoria
            buffer.seek(0)
            if pygame is not None:
                sound = pygame.mixer.Sound(file=buffer)

                with self.cachelock:
                    self.audiocache[text] = sound
                    self.audiocacheorder.append(text)
                    while len(self.audiocacheorder) > self.audiocachemax:
                        viejo = self.audiocacheorder.pop(0)
                        self.audiocache.pop(viejo, None)

                if not self.speaking_cancelled.is_set() and gen == self.speakgen:
                    self.play_sound(sound)

        except (OSError, wave.Error, RuntimeError, ValueError) as error:
            logging.exception("Failed to synthesize speech: %s", error)
        finally:
            if wav_file is not None:
                try:
                    wav_file.close()
                except wave.Error:
                    pass

    def stop(self):
        self.speaking_cancelled.set()
        try:
            with self.playback_lock:
                if self.tts_channel:
                    self.tts_channel.stop()
        except (RuntimeError, OSError):
            pass

    def shutdown(self):
        self.stop()
        if self.speaking_thread is not None and self.speaking_thread.is_alive():
            self.speaking_thread.join(timeout=1.0)
        self.speaking_thread = None
        with self.cachelock:
            self.audiocache.clear()
            self.audiocacheorder.clear()
        self.voice = None

    MAX_LOAD_RETRIES = 3

    def ensure_voice_loaded(self):
        if self.voice:
            return self.voice
        if self.load_error and self.load_retries >= self.MAX_LOAD_RETRIES:
            return None

        with self.load_lock:
            if self.voice:
                return self.voice
            if self.load_error and self.load_retries >= self.MAX_LOAD_RETRIES:
                return None
            try:
                self.voice = PiperVoice.load(
                    str(self.model_path), str(self.config_path)
                )
                self.load_error = None
            except (FileNotFoundError, OSError, RuntimeError, ValueError) as error:
                self.load_retries += 1
                self.load_error = error
                print(
                    f"Warning: Unable to load TTS voice "
                    f"(attempt {self.load_retries}/{self.MAX_LOAD_RETRIES}): {error}"
                )
        return self.voice

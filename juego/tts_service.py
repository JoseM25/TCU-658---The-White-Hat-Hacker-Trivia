import io
import os
import wave
import winsound
from tempfile import NamedTemporaryFile

from piper.voice import PiperVoice


class TTSService:

    def __init__(self, model_dir, model_name="en_US-ryan-high.onnx"):
        self.model_path = model_dir / model_name
        self.config_path = model_dir / f"{model_name}.json"
        self.voice = None
        self.temp_file = None

    def load_voice(self):
        if self.voice:
            return True

        if not self.model_path.exists() or not self.config_path.exists():
            print(f"Piper model files not found in {self.model_path.parent}")
            return False

        try:
            self.voice = PiperVoice.load(
                model_path=str(self.model_path),
                config_path=str(self.config_path),
            )
            return True
        except (OSError, RuntimeError, ValueError) as e:
            print(f"Failed to load Piper voice: {e}")
            return False

    def speak(self, text):
        if not text or not self.load_voice():
            return False

        # Synthesize audio
        audio_bytes = self.synthesize(text)
        if not audio_bytes:
            return False

        # Play audio
        return self.play(audio_bytes)

    def synthesize(self, text):
        buffer = io.BytesIO()

        try:
            with wave.open(buffer, "wb") as wav_file:
                first_chunk = True
                for chunk in self.voice.synthesize(text):
                    if first_chunk:
                        wav_file.setnchannels(chunk.sample_channels)
                        wav_file.setsampwidth(chunk.sample_width)
                        wav_file.setframerate(chunk.sample_rate)
                        first_chunk = False
                    wav_file.writeframes(chunk.audio_int16_bytes)

                if first_chunk:  # No audio was generated
                    return None

            return buffer.getvalue()
        except (wave.Error, OSError, RuntimeError, ValueError) as e:
            print(f"Audio synthesis failed: {e}")
            return None

    def play(self, audio_bytes):
        self.stop()  # Clean up any previous playback

        try:
            # Write to temporary file
            with NamedTemporaryFile(delete=False, suffix=".wav") as f:
                f.write(audio_bytes)
                self.temp_file = f.name

            # Play asynchronously
            winsound.PlaySound(
                self.temp_file, winsound.SND_FILENAME | winsound.SND_ASYNC
            )
            return True
        except (OSError, RuntimeError) as e:
            print(f"Audio playback failed: {e}")
            self._cleanup_temp_file()
            return False

    def stop(self):
        try:
            winsound.PlaySound(None, winsound.SND_PURGE)
        except RuntimeError:
            pass
        self._cleanup_temp_file()

    def _cleanup_temp_file(self):
        if self.temp_file:
            try:
                os.remove(self.temp_file)
            except OSError:
                pass
            self.temp_file = None

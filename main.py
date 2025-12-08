from pathlib import Path

import customtkinter as ctk

from juego.interfaz import AppController
from juego.tts_service import TTSService


BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "recursos" / "audio"

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

root = ctk.CTk()

root.title("White Hat Hacker Trivia!")

root.geometry("1280x720")

root.resizable(True, True)
root.minsize(640, 480)
root.maxsize(3840, 2160)

root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

root.configure(fg_color="#F5F7FA")

# Preload TTS voice once at startup so screens can share it
tts_service = TTSService(AUDIO_DIR)
tts_service.preload()

app = AppController(root, tts_service=tts_service)

root.mainloop()

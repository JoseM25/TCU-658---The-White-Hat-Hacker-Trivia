import customtkinter as ctk

from juego.app_paths import ensure_user_data, get_resource_audio_dir
from juego.interfaz import AppController
from juego.sfx_service import HoverSoundBinder, SFXService
from juego.tts_service import TTSService

AUDIO_DIR = get_resource_audio_dir()

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")
ctk.set_widget_scaling(1.0)
ctk.set_window_scaling(1.0)

root = ctk.CTk()

root.title("The White Hat Hacker Trivia")

root.geometry("1280x720")

root.resizable(True, True)
root.minsize(1280, 720)
root.maxsize(3840, 2160)

root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

root.configure(fg_color="#F5F7FA")

ensure_user_data()

tts_service = TTSService(AUDIO_DIR)
tts_service.preload()

sfx_service = SFXService(AUDIO_DIR)
sfx_service.preload()
hover_binder = HoverSoundBinder(root, sfx_service)

app = AppController(root, tts_service=tts_service, sfx_service=sfx_service)

root.mainloop()

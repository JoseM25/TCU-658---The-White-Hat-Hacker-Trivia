import atexit
import threading

import customtkinter as ctk

from juego.interfaz import AppController
from juego.rutas_app import ensure_user_data, get_resource_audio_dir
from juego.servicio_sfx import HoverSoundBinder, SFXService
from juego.servicio_tts import TTSService

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

sfx_service = SFXService(AUDIO_DIR)
hover_binder = HoverSoundBinder(root, sfx_service)

# Register cleanup on application exit
atexit.register(sfx_service.shutdown)
atexit.register(tts_service.shutdown)


def preloadtodo():
    tts_service.preload()
    sfx_service.preload()


def iniciarprecarga():
    hilo = threading.Thread(target=preloadtodo, daemon=True)
    hilo.start()


root.after(120, iniciarprecarga)

app = AppController(root, tts_service=tts_service, sfx_service=sfx_service)

root.mainloop()

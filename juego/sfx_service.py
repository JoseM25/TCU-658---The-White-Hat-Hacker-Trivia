import logging
import threading
import time
import tkinter as tk
from pathlib import Path

import customtkinter as ctk

try:
    import pygame
except ImportError:
    pygame = None

LOGGER = logging.getLogger(__name__)
PYGAME_EXCEPTIONS = (OSError, RuntimeError)
if pygame is not None:
    pygame_error = getattr(pygame, "error", None)
    if pygame_error is not None:
        PYGAME_EXCEPTIONS = (pygame_error,) + PYGAME_EXCEPTIONS


class SFXService:
    def __init__(self, audio_dir):
        self._audio_dir = Path(audio_dir)
        self._sound_paths = {
            "hover": self._audio_dir / "sfx" / "hover.wav",
            "click": self._audio_dir / "sfx" / "click.wav",
        }
        self._sounds = {}
        self._channels = {}
        self._last_play_time = {}
        self._load_lock = threading.Lock()
        self._enabled = self._init_mixer()

    def _init_mixer(self):
        if pygame is None:
            return False

        try:
            mixer = pygame.mixer
            if not mixer.get_init():
                mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            mixer.set_num_channels(16)
            self._channels["hover"] = mixer.Channel(0)
            self._channels["click"] = mixer.Channel(1)
            return True
        except PYGAME_EXCEPTIONS as exc:
            LOGGER.warning("Failed to init pygame mixer: %s", exc)
            return False

    def preload(self):
        self._load_sound("hover")
        self._load_sound("click")

    def play(self, name, cooldown_ms=0, stop_previous=False, volume=1.0):
        if not self._enabled or pygame is None:
            return

        if name not in self._sounds:
            sound = self._load_sound(name)
        else:
            sound = self._sounds[name]

        if sound is None:
            return

        try:
            if cooldown_ms:
                now = time.monotonic()
                last_time = self._last_play_time.get(name, 0.0)
                if now - last_time < (cooldown_ms / 1000.0):
                    return
                self._last_play_time[name] = now

            mixer = pygame.mixer
            channel = self._channels.get(name) or mixer.find_channel()
            if channel is None:
                return

            if stop_previous:
                channel.stop()

            if volume is not None:
                channel.set_volume(volume)
            channel.play(sound)
        except PYGAME_EXCEPTIONS as exc:
            LOGGER.debug("Failed to play SFX '%s': %s", name, exc)

    def _load_sound(self, name):
        if not self._enabled or pygame is None:
            return None

        if name in self._sounds:
            return self._sounds[name]

        path = self._sound_paths.get(name)
        if not path:
            return None

        with self._load_lock:
            if name in self._sounds:
                return self._sounds[name]

            if not path.exists():
                LOGGER.warning("SFX file not found: %s", path)
                self._sounds[name] = None
                return None

            try:
                sound = pygame.mixer.Sound(str(path))
            except PYGAME_EXCEPTIONS as exc:
                LOGGER.warning("Failed to load SFX '%s': %s", name, exc)
                sound = None

            self._sounds[name] = sound
            return sound


class HoverSoundBinder:
    CLICK_HOOK_INSTALLED = False
    ORIGINAL_CTKBUTTON_INIT = None

    def __init__(self, root, sfx_service):
        self._root = root
        self._sfx = sfx_service
        self._hovered_button = None
        self._hover_cooldown_ms = 80
        self._bind_events()
        self._install_click_hook()

    def _bind_events(self):
        self._root.bind_all("<Enter>", self._on_enter, add="+")
        self._root.bind_all("<Leave>", self._on_leave, add="+")

    def _install_click_hook(self):
        if type(self).CLICK_HOOK_INSTALLED:
            return

        original_init = ctk.CTkButton.__init__

        def _init_with_sfx(button_self, *args, **kwargs):
            original_init(button_self, *args, **kwargs)
            try:
                button_self.bind(
                    "<Button-1>",
                    lambda event, btn=button_self: self._on_button_click(btn),
                    add="+",
                )
            except tk.TclError:
                pass

        ctk.CTkButton.__init__ = _init_with_sfx
        type(self).CLICK_HOOK_INSTALLED = True
        type(self).ORIGINAL_CTKBUTTON_INIT = original_init

    def _on_enter(self, event):
        button = self._find_button(event.widget)
        if not button or not button.winfo_exists():
            return

        try:
            if button.cget("state") != "normal":
                return
        except tk.TclError:
            return

        if button is self._hovered_button:
            return

        self._hovered_button = button
        self._sfx.play("hover", cooldown_ms=self._hover_cooldown_ms, stop_previous=True)

    def _on_button_click(self, button):
        try:
            if button.cget("state") != "normal":
                return
        except tk.TclError:
            return
        self._sfx.play("click", stop_previous=True)

    def _on_leave(self, event):
        if not self._hovered_button:
            return

        widget = self._root.winfo_containing(event.x_root, event.y_root)
        button = self._find_button(widget)
        if button is self._hovered_button:
            return

        self._hovered_button = None

    @staticmethod
    def _find_button(widget):
        while widget is not None:
            if isinstance(widget, ctk.CTkButton):
                return widget
            widget = getattr(widget, "master", None)
        return None

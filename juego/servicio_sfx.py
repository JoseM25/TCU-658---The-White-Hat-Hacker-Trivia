import logging
import threading
import time
import tkinter as tk
import weakref
from pathlib import Path

import customtkinter as ctk

try:
    import pygame
except ImportError:
    pygame = None

LOGGER = logging.getLogger(__name__)
PYGAME_EXCEPTIONS = (OSError, RuntimeError)
if pygame is not None:
    PYGAME_ERROR = getattr(pygame, "error", None)
    if PYGAME_ERROR is not None:
        PYGAME_EXCEPTIONS = (PYGAME_ERROR,) + PYGAME_EXCEPTIONS


class SFXService:
    def __init__(self, audio_dir):
        self.audio_dir = Path(audio_dir)
        self.sound_paths = {
            "hover": self.audio_dir / "sfx" / "hover.wav",
            "click": self.audio_dir / "sfx" / "click.wav",
            "correct": self.audio_dir / "sfx" / "correct.wav",
            "incorrect": self.audio_dir / "sfx" / "incorrect.wav",
            "freeze": self.audio_dir / "sfx" / "freeze.wav",
            "points": self.audio_dir / "sfx" / "points.wav",
            "reveal": self.audio_dir / "sfx" / "reveal.wav",
            "win": self.audio_dir / "sfx" / "win.wav",
        }
        self.sounds = {}
        self.channels = {}
        self.last_play_time = {}
        self.load_lock = threading.Lock()
        self.enabled = self.init_mixer()
        self.muted = False

    def init_mixer(self):
        if pygame is None:
            return False

        try:
            mixer = pygame.mixer
            if not mixer.get_init():
                mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            mixer.set_num_channels(16)
            self.channels["hover"] = mixer.Channel(0)
            self.channels["click"] = mixer.Channel(1)
            return True
        except PYGAME_EXCEPTIONS as exc:
            LOGGER.warning("Failed to init pygame mixer: %s", exc)
            return False

    def preload(self):
        self.load_sound("hover")
        self.load_sound("click")
        self.load_sound("correct")
        self.load_sound("incorrect")
        self.load_sound("freeze")
        self.load_sound("points")
        self.load_sound("reveal")
        self.load_sound("win")

    def shutdown(self):
        """Properly shut down the pygame mixer. Call on application exit."""
        if not self.enabled or pygame is None:
            return
        try:
            pygame.mixer.stop()
            pygame.mixer.quit()
        except PYGAME_EXCEPTIONS as exc:
            LOGGER.debug("Failed to shutdown mixer: %s", exc)
        self.enabled = False
        self.sounds.clear()
        self.channels.clear()

    def set_muted(self, muted):
        self.muted = bool(muted)
        if self.muted and self.enabled and pygame is not None:
            try:
                pygame.mixer.stop()
            except PYGAME_EXCEPTIONS as exc:
                LOGGER.debug("Failed to stop SFX: %s", exc)

    def is_muted(self):
        return self.muted

    def play(self, name, cooldown_ms=0, stop_previous=False, volume=1.0):
        if not self.enabled or pygame is None or self.muted:
            return

        if name not in self.sounds:
            sound = self.load_sound(name)
        else:
            sound = self.sounds[name]

        if sound is None:
            return

        try:
            if cooldown_ms:
                now = time.monotonic()
                last_time = self.last_play_time.get(name, 0.0)
                if now - last_time < (cooldown_ms / 1000.0):
                    return
                self.last_play_time[name] = now

            mixer = pygame.mixer
            channel = self.channels.get(name) or mixer.find_channel()
            if channel is None:
                return

            if stop_previous:
                channel.stop()

            if volume is not None:
                channel.set_volume(volume)
            channel.play(sound)
        except PYGAME_EXCEPTIONS as exc:
            LOGGER.debug("Failed to play SFX '%s': %s", name, exc)

    def load_sound(self, name):
        if not self.enabled or pygame is None:
            return None

        if name in self.sounds:
            return self.sounds[name]

        path = self.sound_paths.get(name)
        if not path:
            return None

        with self.load_lock:
            if name in self.sounds:
                return self.sounds[name]

            if not path.exists():
                LOGGER.warning("SFX file not found: %s", path)
                self.sounds[name] = None
                return None

            try:
                sound = pygame.mixer.Sound(str(path))
            except PYGAME_EXCEPTIONS as exc:
                LOGGER.warning("Failed to load SFX '%s': %s", name, exc)
                sound = None

            self.sounds[name] = sound
            return sound


class HoverSoundBinder:
    CLICK_HOOK_INSTALLED = False
    ORIGINAL_CTKBUTTON_CLICKED = None
    # Class-level weak reference to the active SFX service for click sounds
    _active_sfx_ref = None

    def __init__(self, root, sfx_service):
        self.root = root
        self.sfx = sfx_service
        self.hovered_button = None
        self.hover_cooldown_ms = 80
        # Store weak reference at class level so the closure doesn't hold strong ref
        HoverSoundBinder._active_sfx_ref = weakref.ref(sfx_service)
        self.bind_events()
        self.install_click_hook()

    def bind_events(self):
        self.root.bind_all("<Enter>", self.on_enter, add="+")
        self.root.bind_all("<Leave>", self.on_leave, add="+")

    def unbind_events(self):
        """Unbind hover events. Call this on cleanup."""
        try:
            self.root.unbind_all("<Enter>")
        except tk.TclError:
            pass
        try:
            self.root.unbind_all("<Leave>")
        except tk.TclError:
            pass

    def install_click_hook(self):
        if type(self).CLICK_HOOK_INSTALLED:
            return

        original_clicked = getattr(ctk.CTkButton, "_clicked")

        def clicked_with_sfx(button_self, event=None):
            # Use class-level weak reference instead of capturing self
            sfx_ref = HoverSoundBinder._active_sfx_ref
            if sfx_ref is not None:
                sfx = sfx_ref()
                if sfx is not None:
                    try:
                        if button_self.cget("state") == "normal":
                            sfx.play("click", stop_previous=True, volume=0.8)
                    except tk.TclError:
                        pass
            return original_clicked(button_self, event)

        setattr(ctk.CTkButton, "_clicked", clicked_with_sfx)
        type(self).CLICK_HOOK_INSTALLED = True
        type(self).ORIGINAL_CTKBUTTON_CLICKED = original_clicked

    def on_enter(self, event):
        button = self.find_button(event.widget)
        if not button or not button.winfo_exists():
            return

        try:
            if button.cget("state") != "normal":
                return
        except tk.TclError:
            return

        if button is self.hovered_button:
            return

        self.hovered_button = button
        self.sfx.play("hover", cooldown_ms=self.hover_cooldown_ms, stop_previous=True)

    def on_button_click(self, button, force=False):
        if not force:
            try:
                if button.cget("state") != "normal":
                    return
            except tk.TclError:
                return
        self.sfx.play("click", stop_previous=True, volume=0.8)

    def on_click_event(self, event):
        button = self.find_button(event.widget)
        if not button:
            return
        self.on_button_click(button, force=True)

    def on_leave(self, event):
        if not self.hovered_button:
            return

        widget = self.root.winfo_containing(event.x_root, event.y_root)
        button = self.find_button(widget)
        if button is self.hovered_button:
            return

        self.hovered_button = None

    @staticmethod
    def find_button(widget):
        while widget is not None:
            if isinstance(widget, ctk.CTkButton):
                return widget
            widget = getattr(widget, "master", None)
        return None

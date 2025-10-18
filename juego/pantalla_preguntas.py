import io
import json
import os
import threading
import tkinter as tk
import wave
from pathlib import Path
from tempfile import NamedTemporaryFile
import winsound

import customtkinter as ctk
from PIL import Image, ImageTk, UnidentifiedImageError
from piper.voice import PiperVoice
from tksvg import SvgImage as TkSvgImage


class ManageQuestionsScreen:
    HEADER_TEXT = "Manage Questions"
    MAX_VISIBLE_QUESTIONS = 8
    QUESTIONS_FILE = Path(__file__).resolve().parent.parent / "datos" / "preguntas.json"
    IMAGES_DIR = Path(__file__).resolve().parent.parent / "recursos" / "imagenes"
    DETAIL_IMAGE_MAX_SIZE = (220, 220)
    AUDIO_ICON_FILENAME = "volume.svg"
    AUDIO_ICON_SIZE = (32, 32)
    SVG_RASTER_SCALE = 2.0
    QUESTION_DEFAULT_BG = "transparent"
    QUESTION_DEFAULT_TEXT = "#1F2937"
    QUESTION_DEFAULT_HOVER = "#E2E8F0"
    QUESTION_SELECTED_BG = "#1D6CFF"
    QUESTION_BUTTON_SIDE_MARGIN = 1
    QUESTION_BUTTON_HEIGHT = 50
    QUESTION_BUTTON_VERTICAL_PADDING = 1
    AUDIO_DIR = Path(__file__).resolve().parent.parent / "recursos" / "audio"
    PIPER_MODEL_FILENAME = "en_US-ryan-high.onnx"
    PIPER_CONFIG_FILENAME = "en_US-ryan-high.onnx.json"

    def __init__(self, parent, on_return_callback=None):
        self.parent = parent
        self.on_return_callback = on_return_callback
        self.detail_visible = False
        self.selected_question_button = None
        self.question_selected_text_color = "#FFFFFF"
        self.questions = self.load_questions()
        self.current_image_path = ""
        self.add_button: None
        self.detail_container: None
        self.detail_title_label: None
        self.edit_button: None
        self.delete_button: None
        self.detail_image_label: None
        self.detail_definition_label: None
        self.definition_audio_button: None
        self.definition_audio_image = None
        self.detail_image = None
        self.current_question = None
        self.audio_thread = None
        self.voice = None
        self.voice_error = None
        self.playback_error = None
        self._active_audio_temp_path = None
        self.piper_model_path = self.AUDIO_DIR / self.PIPER_MODEL_FILENAME
        self.piper_config_path = self.AUDIO_DIR / self.PIPER_CONFIG_FILENAME

        for widget in self.parent.winfo_children():
            widget.destroy()

        self.title_font = ctk.CTkFont(
            family="Poppins ExtraBold",
            size=38,
            weight="bold",
        )
        self.body_font = ctk.CTkFont(family="Poppins Medium", size=18)
        self.button_font = ctk.CTkFont(
            family="Poppins SemiBold", size=16, weight="bold"
        )
        self.search_font = ctk.CTkFont(
            family="Poppins SemiBold", size=18, weight="bold"
        )
        self.question_font = ctk.CTkFont(
            family="Poppins SemiBold",
            size=18,
            weight="bold",
        )
        self.detail_title_font = ctk.CTkFont(
            family="Poppins ExtraBold",
            size=38,
            weight="bold",
        )

        self.build_ui()

    def load_questions(self):
        if not self.QUESTIONS_FILE.exists():
            return []

        try:
            data = json.loads(self.QUESTIONS_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []

        if isinstance(data, dict):
            raw_questions = data.get("questions", [])
        else:
            raw_questions = data

        questions = []
        for item in raw_questions:
            if not isinstance(item, dict):
                continue

            title = (item.get("title") or "").strip()
            if not title:
                continue

            definition = (item.get("definition") or "").strip()
            image = (item.get("image") or "").strip()
            audio = (item.get("audio") or "").strip()

            questions.append(
                {
                    "title": title,
                    "definition": definition,
                    "image": image,
                    "audio": audio,
                }
            )

        return questions

    def build_ui(self):
        self.parent.grid_rowconfigure(0, weight=1)
        self.parent.grid_columnconfigure(0, weight=1)

        self.main = ctk.CTkFrame(self.parent, fg_color="transparent")
        self.main.grid(row=0, column=0, sticky="nsew")
        self.main.grid_rowconfigure(1, weight=1)
        self.main.grid_columnconfigure(0, weight=0)
        self.main.grid_columnconfigure(1, weight=0, minsize=2)
        self.main.grid_columnconfigure(2, weight=1)

        self.build_header()
        self.build_content()

    def build_header(self):
        header = ctk.CTkFrame(
            self.main,
            fg_color="#1C2534",
            corner_radius=0,
        )
        header.grid(row=0, column=0, columnspan=3, sticky="ew")
        header.grid_columnconfigure(0, weight=0)
        header.grid_columnconfigure(1, weight=1)

        back_button = ctk.CTkButton(
            header,
            text="< Menu",
            font=self.button_font,
            text_color="#FFFFFF",
            fg_color="transparent",
            hover_color="#273246",
            command=self.return_to_menu,
            corner_radius=8,
            border_width=0,
            width=110,
            height=44,
        )
        back_button.grid(row=0, column=0, padx=(24, 16), pady=(28, 32), sticky="w")

        title = ctk.CTkLabel(
            header,
            text=self.HEADER_TEXT,
            font=self.title_font,
            text_color="#FFFFFF",
            anchor="center",
            justify="center",
        )
        title.grid(row=0, column=1, padx=32, pady=(28, 32), sticky="nsew")

    def build_content(self):
        sidebar = ctk.CTkFrame(self.main, fg_color="transparent")
        sidebar.grid(row=1, column=0, sticky="ns", padx=(32, 12), pady=32)
        sidebar.grid_rowconfigure(1, weight=1)
        sidebar.grid_columnconfigure(0, weight=1)

        self.build_controls(sidebar)
        self.build_question_list(sidebar)

        divider = ctk.CTkFrame(
            self.main,
            fg_color="#D2DAE6",
            corner_radius=0,
            width=2,
        )
        divider.grid(row=1, column=1, sticky="ns", pady=32)

        detail_container = ctk.CTkFrame(
            self.main,
            fg_color="#F5F7FA",
            corner_radius=16,
            border_width=1,
            border_color="#D2DAE6",
        )
        detail_container.grid(row=1, column=2, sticky="nsew", padx=(12, 32), pady=32)
        detail_container.grid_rowconfigure(0, weight=0)
        detail_container.grid_rowconfigure(1, weight=1)
        detail_container.grid_columnconfigure(0, weight=1)

        detail_header = ctk.CTkFrame(
            detail_container,
            fg_color="transparent",
        )
        detail_header.grid(row=0, column=0, sticky="ew", padx=24, pady=(24, 12))
        detail_header.grid_columnconfigure(0, weight=1)
        detail_header.grid_columnconfigure(1, weight=0)
        detail_header.grid_columnconfigure(2, weight=0)

        self.detail_title_label = ctk.CTkLabel(
            detail_header,
            text="",
            font=self.detail_title_font,
            text_color="#111827",
            anchor="w",
            justify="left",
        )
        self.detail_title_label.grid(row=0, column=0, sticky="w", padx=(12, 0))

        self.edit_button = ctk.CTkButton(
            detail_header,
            text="Edit",
            font=self.question_font,
            fg_color="#00CFC5",
            hover_color="#04AFA6",
            command=self.on_edit_pressed,
            width=110,
            height=44,
            corner_radius=12,
        )
        self.edit_button.grid(row=0, column=1, padx=(12, 12), sticky="e")

        self.delete_button = ctk.CTkButton(
            detail_header,
            text="Delete",
            font=self.question_font,
            fg_color="#FF4F60",
            hover_color="#E53949",
            command=self.on_delete_pressed,
            width=110,
            height=44,
            corner_radius=12,
        )
        self.delete_button.grid(row=0, column=2, sticky="e")

        detail_body = ctk.CTkFrame(
            detail_container,
            fg_color="transparent",
        )
        detail_body.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 24))
        detail_body.grid_rowconfigure(0, weight=1)
        detail_body.grid_columnconfigure(0, weight=1)

        detail_content = ctk.CTkFrame(
            detail_body,
            fg_color="transparent",
        )
        detail_content.grid(row=0, column=0, sticky="n")
        detail_content.grid_columnconfigure(0, weight=1)

        self.detail_image_label = ctk.CTkLabel(
            detail_content,
            text="Image placeholder",
            font=self.search_font,
            text_color="#4B5563",
            fg_color="transparent",
            width=220,
            height=220,
            corner_radius=0,
            anchor="center",
        )
        self.detail_image_label.grid(
            row=0, column=0, pady=(28, 48), padx=12, sticky="n"
        )

        definition_row = ctk.CTkFrame(
            detail_content,
            fg_color="transparent",
        )
        definition_row.grid(row=1, column=0, sticky="ew", padx=32, pady=(32, 0))
        definition_row.grid_columnconfigure(0, weight=0)
        definition_row.grid_columnconfigure(1, weight=1)

        audio_image_loaded = self.ensure_audio_icon()
        button_kwargs = {}
        if audio_image_loaded:
            button_kwargs["image"] = self.definition_audio_image
            button_kwargs["text"] = ""
        else:
            button_kwargs["text"] = "Audio"
            button_kwargs["font"] = self.body_font
            button_kwargs["text_color"] = "#1F2937"

        self.definition_audio_button = ctk.CTkButton(
            definition_row,
            fg_color="transparent",
            hover_color="#E5E7EB",
            border_width=0,
            width=44,
            height=44,
            corner_radius=22,
            command=self.on_definition_audio_pressed,
            **button_kwargs,
        )
        self.definition_audio_button.grid(row=0, column=0, sticky="nw", padx=(0, 16))
        self.definition_audio_button.configure(state="disabled")

        self.detail_definition_label = ctk.CTkLabel(
            definition_row,
            text="",
            font=self.body_font,
            text_color="#1F2937",
            justify="left",
            anchor="w",
            wraplength=540,
        )
        self.detail_definition_label.grid(row=0, column=1, sticky="nw")

        self.detail_container = detail_container
        self.detail_container.grid_remove()
        self.detail_visible = False

    def build_controls(self, container):
        controls = ctk.CTkFrame(
            container,
            fg_color="transparent",
        )
        controls.grid(row=0, column=0, sticky="ew")
        controls.grid_columnconfigure(0, weight=1)
        controls.grid_columnconfigure(1, weight=0)
        search_entry = ctk.CTkEntry(
            controls,
            placeholder_text="Search...",
            placeholder_text_color="#F5F7FA",
            fg_color="#D1D8E0",
            font=self.search_font,
            corner_radius=18,
            height=42,
            border_width=0,
        )
        search_entry.grid(row=0, column=0, padx=(16, 12), pady=16, sticky="ew")

        add_button = ctk.CTkButton(
            controls,
            text="Add",
            font=self.button_font,
            fg_color="#1D6CFF",
            hover_color="#0F55C9",
            command=self.on_add_pressed,
            width=96,
            height=42,
            corner_radius=12,
        )
        add_button.grid(row=0, column=1, padx=(0, 16), pady=16)
        self.add_button = add_button
        resolved_text_color = add_button.cget("text_color")
        if resolved_text_color:
            self.question_selected_text_color = resolved_text_color

    def build_question_list(self, container):
        needs_scrollbar = len(self.questions) > self.MAX_VISIBLE_QUESTIONS

        frame_kwargs = {
            "fg_color": "#F5F7FA",
            "border_width": 1,
            "border_color": "#D2DAE6",
            "corner_radius": 24,
        }

        list_container = ctk.CTkFrame(
            container,
            fg_color="transparent",
        )
        list_container.grid(row=1, column=0, sticky="nsew", pady=(20, 0))
        list_container.grid_columnconfigure(0, weight=1)
        list_container.grid_rowconfigure(0, weight=1)

        if needs_scrollbar:
            list_frame = ctk.CTkScrollableFrame(
                list_container,
                **frame_kwargs,
            )
        else:
            list_frame = ctk.CTkFrame(
                list_container,
                **frame_kwargs,
            )

        list_frame.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        if needs_scrollbar:
            for child in list_frame.winfo_children():
                if isinstance(child, ctk.CTkScrollbar):
                    child.grid_configure(padx=(0, 6), pady=(6, 6))
                    break

        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, minsize=24)

        self.selected_question_button = None

        if not self.questions:
            empty_label = ctk.CTkLabel(
                list_frame,
                text="No questions available.",
                font=self.body_font,
                text_color="#6B7280",
            )
            empty_label.grid(row=1, column=0, padx=24, pady=(12, 24), sticky="nsew")
            list_frame.grid_rowconfigure(1, weight=1)
            return

        for index, question in enumerate(self.questions, start=1):
            button = ctk.CTkButton(
                list_frame,
                text=question.get("title", ""),
                font=self.question_font,
                text_color=self.QUESTION_DEFAULT_TEXT,
                fg_color=self.QUESTION_DEFAULT_BG,
                hover_color=self.QUESTION_DEFAULT_HOVER,
                border_width=0,
                height=self.QUESTION_BUTTON_HEIGHT,
            )
            button.configure(
                command=lambda q=question, b=button: self.show_question_details(q, b)
            )
            button.grid(
                row=index,
                column=0,
                sticky="nsew",
                padx=(
                    self.QUESTION_BUTTON_SIDE_MARGIN,
                    self.QUESTION_BUTTON_SIDE_MARGIN,
                ),
                pady=(
                    (0 if index == 1 else self.QUESTION_BUTTON_VERTICAL_PADDING),
                    self.QUESTION_BUTTON_VERTICAL_PADDING,
                ),
            )
            list_frame.grid_rowconfigure(index, weight=0)

        list_frame.grid_columnconfigure(0, weight=1)

    def on_add_pressed(self):
        # Placeholder for future add-question flow
        pass

    def on_edit_pressed(self):
        # Placeholder for future edit-question flow
        pass

    def on_delete_pressed(self):
        # Placeholder for future delete-question flow
        pass

    def on_definition_audio_pressed(self):
        if not self.current_question:
            return

        definition = (self.current_question.get("definition") or "").strip()
        if not definition:
            return

        if not self.ensure_voice():
            return

        self.stop_definition_audio()

        self.audio_thread = threading.Thread(
            target=self.speak_definition_async,
            args=(definition,),
            daemon=True,
        )
        self.audio_thread.start()

    def return_to_menu(self):
        self.stop_definition_audio()
        if self.on_return_callback:
            self.on_return_callback()

    def load_svg_image(self, svg_path, scale=1.0):
        try:
            svg_photo = TkSvgImage(file=str(svg_path), scale=scale)
            pil_image = ImageTk.getimage(svg_photo).convert("RGBA")
            return pil_image
        except (FileNotFoundError, ValueError):
            return None

    def ensure_audio_icon(self):
        if self.definition_audio_image:
            return True

        svg_path = self.IMAGES_DIR / self.AUDIO_ICON_FILENAME
        pil_image = self.load_svg_image(svg_path, scale=self.SVG_RASTER_SCALE)
        if not pil_image:
            return False

        self.definition_audio_image = ctk.CTkImage(
            light_image=pil_image,
            dark_image=pil_image,
            size=self.AUDIO_ICON_SIZE,
        )
        return True

    def resolve_image_path(self, image_path):
        if not image_path:
            return None

        candidate = Path(image_path)
        if not candidate.is_absolute():
            candidate = Path(__file__).resolve().parent.parent / candidate

        if candidate.exists():
            return candidate
        return None

    def create_detail_ctk_image(self, image_file):
        resample_source = getattr(Image, "Resampling", Image)
        resample_method = getattr(
            resample_source, "LANCZOS", getattr(resample_source, "BICUBIC", 3)
        )

        try:
            with Image.open(image_file) as loaded_image:
                image_rgba = loaded_image.convert("RGBA")
                prepared_image = image_rgba.copy()
        except (FileNotFoundError, UnidentifiedImageError, OSError, ValueError):
            return None

        width, height = prepared_image.size
        if width <= 0 or height <= 0:
            return None

        max_width, max_height = self.DETAIL_IMAGE_MAX_SIZE
        width_scale = max_width / width
        height_scale = max_height / height
        scale = min(width_scale, height_scale, 1)

        scaled_size = (
            max(1, int(round(width * scale))),
            max(1, int(round(height * scale))),
        )

        if scale < 1:
            prepared_image = prepared_image.resize(scaled_size, resample_method)

        return ctk.CTkImage(
            light_image=prepared_image,
            dark_image=prepared_image,
            size=scaled_size,
        )

    def update_detail_image(self):
        if not self.detail_image_label or not self.detail_image_label.winfo_exists():
            return

        resolved_path = self.resolve_image_path(self.current_image_path)
        if not resolved_path:
            try:
                self.detail_image_label.configure(
                    image=None,
                    text="Image not available",
                )
            except tk.TclError:
                return
            self.detail_image_label.image = None
            self.detail_image = None
            return

        loaded_image = self.create_detail_ctk_image(resolved_path)
        if loaded_image is None:
            try:
                self.detail_image_label.configure(
                    image=None,
                    text="Image not available",
                )
            except tk.TclError:
                return
            self.detail_image_label.image = None
            self.detail_image = None
            return

        try:
            self.detail_image_label.configure(image=loaded_image, text="")
        except tk.TclError:
            try:
                self.detail_image_label.configure(
                    image=None,
                    text="Image not available",
                )
            except tk.TclError:
                return
            self.detail_image_label.image = None
            self.detail_image = None
            return

        self.detail_image = loaded_image
        self.detail_image_label.image = loaded_image

    def show_question_details(self, question, button):
        self.stop_definition_audio()

        if not self.detail_visible:
            self.detail_container.grid()
            self.detail_visible = True

        if (
            self.selected_question_button
            and self.selected_question_button is not button
        ):
            self.selected_question_button.configure(
                fg_color=self.QUESTION_DEFAULT_BG,
                text_color=self.QUESTION_DEFAULT_TEXT,
                hover_color=self.QUESTION_DEFAULT_HOVER,
            )

        button.configure(
            fg_color=self.QUESTION_SELECTED_BG,
            text_color=self.question_selected_text_color,
            hover_color=self.QUESTION_SELECTED_BG,
        )
        self.selected_question_button = button

        title = question.get("title", "")
        raw_definition = question.get("definition") or ""
        definition = raw_definition or "No definition available yet."
        self.current_image_path = question.get("image", "")
        self.current_question = question
        self.update_detail_image()

        if self.definition_audio_button:
            if raw_definition.strip():
                self.definition_audio_button.configure(state="normal")
            else:
                self.definition_audio_button.configure(state="disabled")

        self.detail_title_label.configure(text=title)
        self.detail_definition_label.configure(text=definition)

    def stop_definition_audio(self):
        if winsound is not None:
            try:
                winsound.PlaySound(None, winsound.SND_PURGE)
            except RuntimeError:
                pass
        self.cleanup_temp_audio_file()
        self.audio_thread = None

    def ensure_voice(self):
        if self.voice:
            return True

        if not self.piper_model_path.exists():
            message = f"Piper model file not found at: {self.piper_model_path}"
            if self.voice_error != message:
                print(message)
            self.voice_error = message
            return False

        if not self.piper_config_path.exists():
            message = f"Piper config file not found at: {self.piper_config_path}"
            if self.voice_error != message:
                print(message)
            self.voice_error = message
            return False

        try:
            self.voice = PiperVoice.load(
                model_path=str(self.piper_model_path),
                config_path=str(self.piper_config_path),
            )
            self.voice_error = None
        except FileNotFoundError as exc:
            message = f"Unable to open Piper files: {exc}"
            if self.voice_error != message:
                print(message)
            self.voice = None
            self.voice_error = message
            return False
        except (OSError, RuntimeError, ValueError) as exc:
            message = f"Unable to initialize Piper voice: {exc}"
            if self.voice_error != message:
                print(message)
            self.voice = None
            self.voice_error = message
            return False

        return True

    def cleanup_temp_audio_file(self):
        if not self._active_audio_temp_path:
            return

        try:
            os.remove(self._active_audio_temp_path)
        except OSError:
            pass

        self._active_audio_temp_path = None

    def synthesize_definition_audio(self, text):
        if not text or not self.voice:
            return None

        buffer = io.BytesIO()
        wrote_audio = False

        try:
            with wave.open(buffer, "wb") as wav_file:
                for chunk in self.voice.synthesize(text):
                    if not wrote_audio:
                        wav_file.setnchannels(chunk.sample_channels)
                        wav_file.setsampwidth(chunk.sample_width)
                        wav_file.setframerate(chunk.sample_rate)
                        wrote_audio = True
                    wav_file.writeframes(chunk.audio_int16_bytes)
        except (wave.Error, OSError, RuntimeError, ValueError, AttributeError) as exc:
            message = f"Unable to synthesize Piper audio: {exc}"
            if self.playback_error != message:
                print(message)
            self.playback_error = message
            return None

        if not wrote_audio:
            message = "Piper synthesis returned no audio data."
            if self.playback_error != message:
                print(message)
            self.playback_error = message
            return None

        self.playback_error = None
        return buffer.getvalue()

    def play_audio_bytes(self, audio_bytes):
        if not audio_bytes:
            return

        if winsound is None:
            message = "Audio playback is not supported on this platform."
            if self.playback_error != message:
                print(message)
            self.playback_error = message
            return

        self.cleanup_temp_audio_file()

        temp_path = None
        try:
            with NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                temp_file.write(audio_bytes)
                temp_path = temp_file.name

            winsound.PlaySound(
                temp_path,
                winsound.SND_FILENAME | winsound.SND_ASYNC,
            )
            self._active_audio_temp_path = temp_path
            self.playback_error = None
        except (OSError, RuntimeError) as exc:
            message = f"Piper playback failed: {exc}"
            if self.playback_error != message:
                print(message)
            self.playback_error = message
            if temp_path:
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    def speak_definition_async(self, text):
        if not text or not self.voice:
            return

        try:
            audio_bytes = self.synthesize_definition_audio(text)
            if not audio_bytes:
                return

            if threading.current_thread() is not self.audio_thread:
                return

            self.play_audio_bytes(audio_bytes)
        finally:
            if threading.current_thread() is self.audio_thread:
                self.audio_thread = None

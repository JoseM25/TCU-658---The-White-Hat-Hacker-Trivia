import json
import tkinter as tk
from pathlib import Path

import customtkinter as ctk
from PIL import Image, ImageTk
from tksvg import SvgImage as TkSvgImage

from juego.tts_service import TTSService


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

        # Initialize TTS service
        self.tts = TTSService(self.AUDIO_DIR)

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

        # Try to load audio icon, fallback to text
        self.ensure_audio_icon()

        self.definition_audio_button = ctk.CTkButton(
            definition_row,
            text="" if self.definition_audio_image else "Audio",
            image=self.definition_audio_image if self.definition_audio_image else None,
            font=self.body_font if not self.definition_audio_image else None,
            text_color="#1F2937" if not self.definition_audio_image else None,
            fg_color="transparent",
            hover_color="#E5E7EB",
            border_width=0,
            width=44,
            height=44,
            corner_radius=22,
            command=self.on_definition_audio_pressed,
            state="disabled",
        )
        self.definition_audio_button.grid(row=0, column=0, sticky="nw", padx=(0, 16))

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
        if definition:
            self.tts.speak(definition)

    def return_to_menu(self):
        self.tts.stop()
        if self.on_return_callback:
            self.on_return_callback()

    def load_svg_image(self, svg_path, scale=1.0):
        try:
            svg_photo = TkSvgImage(file=str(svg_path), scale=scale)
            return ImageTk.getimage(svg_photo).convert("RGBA")
        except (FileNotFoundError, OSError, ValueError, RuntimeError):
            return None

    def ensure_audio_icon(self):
        if self.definition_audio_image:
            return

        svg_path = self.IMAGES_DIR / self.AUDIO_ICON_FILENAME
        pil_image = self.load_svg_image(svg_path, scale=self.SVG_RASTER_SCALE)

        if pil_image:
            self.definition_audio_image = ctk.CTkImage(
                light_image=pil_image,
                dark_image=pil_image,
                size=self.AUDIO_ICON_SIZE,
            )

    def resolve_image_path(self, image_path):
        if not image_path:
            return None

        candidate = Path(image_path)
        if not candidate.is_absolute():
            candidate = Path(__file__).resolve().parent.parent / candidate

        return candidate if candidate.exists() else None

    def create_detail_ctk_image(self, image_file):
        try:
            with Image.open(image_file) as img:
                prepared_image = img.convert("RGBA").copy()
        except (FileNotFoundError, OSError, ValueError):
            return None

        width, height = prepared_image.size
        if width <= 0 or height <= 0:
            return None

        # Calculate scale to fit within max size
        max_width, max_height = self.DETAIL_IMAGE_MAX_SIZE
        scale = min(max_width / width, max_height / height, 1)

        if scale < 1:
            new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
            resample = getattr(Image.Resampling, "LANCZOS", 1)
            prepared_image = prepared_image.resize(new_size, resample)

        return ctk.CTkImage(
            light_image=prepared_image,
            dark_image=prepared_image,
            size=prepared_image.size,
        )

    def update_detail_image(self):
        if not self.detail_image_label or not self.detail_image_label.winfo_exists():
            return

        # Try to load and display image
        resolved_path = self.resolve_image_path(self.current_image_path)
        loaded_image = (
            self.create_detail_ctk_image(resolved_path) if resolved_path else None
        )

        try:
            if loaded_image:
                self.detail_image_label.configure(image=loaded_image, text="")
                self.detail_image = loaded_image
                self.detail_image_label.image = loaded_image
            else:
                self.detail_image_label.configure(
                    image=None, text="Image not available"
                )
                self.detail_image = None
                self.detail_image_label.image = None
        except tk.TclError:
            pass

    def show_question_details(self, question, button):
        self.tts.stop()

        # Show detail panel if hidden
        if not self.detail_visible:
            self.detail_container.grid()
            self.detail_visible = True

        # Update button selection states
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

        # Update detail content
        title = question.get("title", "")
        raw_definition = (question.get("definition") or "").strip()
        definition = raw_definition or "No definition available yet."

        self.current_question = question
        self.current_image_path = question.get("image", "")
        self.update_detail_image()

        # Enable/disable audio button based on definition availability
        if self.definition_audio_button:
            self.definition_audio_button.configure(
                state="normal" if raw_definition else "disabled"
            )

        self.detail_title_label.configure(text=title)
        self.detail_definition_label.configure(text=definition)

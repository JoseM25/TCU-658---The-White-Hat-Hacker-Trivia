import json
import tkinter as tk
from pathlib import Path
from tkinter import messagebox
from types import SimpleNamespace

import customtkinter as ctk

from juego.tts_service import TTSService
from juego.image_handler import ImageHandler
from juego.preguntas_modales import (
    AddQuestionModal,
    EditQuestionModal,
    DeleteConfirmationModal,
)


class QuestionPersistenceError(Exception):
    """Raised when the questions file cannot be updated."""


class QuestionFileStorage:
    """Handles file I/O for questions data."""

    def __init__(self, json_path):
        self.json_path = Path(json_path)

    def load_questions(self):
        """Load and parse questions from JSON file."""
        if not self.json_path.exists():
            return []

        try:
            raw_text = self.json_path.read_text(encoding="utf-8")
        except OSError as error:
            print(f"Warning: Unable to read {self.json_path}: {error}")
            return []

        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError:
            return []

        raw_questions = (
            data.get("questions", []) if hasattr(data, "get") else (data or [])
        )

        normalized = []
        for item in raw_questions:
            if not hasattr(item, "get"):
                continue
            title = (item.get("title") or "").strip()
            if not title:
                continue
            definition = (item.get("definition") or "").strip()
            image = (item.get("image") or "").strip()
            normalized.append(
                {"title": title, "definition": definition, "image": image}
            )

        return normalized

    def save_questions(self, questions):
        """Save questions list to JSON file."""
        payload = {"questions": questions}
        try:
            self.json_path.parent.mkdir(parents=True, exist_ok=True)
            self.json_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as error:
            raise QuestionPersistenceError(
                f"Unable to write {self.json_path}: {error}"
            ) from error


class QuestionRepository:
    """Manages question data with CRUD operations."""

    def __init__(self, json_path):
        self.storage = QuestionFileStorage(json_path)
        self.questions = []
        self.load()

    def load(self):
        """Load questions from storage."""
        self.questions = self.storage.load_questions()
        return self.questions

    def save(self, questions):
        """Save questions to storage and update local cache."""
        self.storage.save_questions(questions)
        self.questions = list(questions)
        return self.questions

    def add_question(self, title, definition, image_path):
        new_question = {"title": title, "definition": definition, "image": image_path}
        self.save([*self.questions, new_question])
        return new_question

    def update_question(self, old_question, title, definition, image_path):
        updated_question = {
            "title": title,
            "definition": definition,
            "image": image_path,
        }
        try:
            index = self.questions.index(old_question)
        except ValueError:
            index = None

        updated_questions = [q for q in self.questions if q is not old_question]
        insert_index = index if index is not None else len(updated_questions)
        updated_questions.insert(insert_index, updated_question)
        self.save(updated_questions)
        return self.questions[insert_index]

    def delete_question(self, question):
        try:
            index = self.questions.index(question)
        except ValueError:
            return False

        updated_questions = self.questions[:index] + self.questions[index + 1 :]
        self.save(updated_questions)
        return True

    def is_title_unique(self, title, exclude_question=None):
        normalized = (title or "").strip().lower()
        for question in self.questions:
            if question is exclude_question:
                continue
            if question.get("title", "").strip().lower() == normalized:
                return False
        return True


class ManageQuestionsScreen:

    BASE_DIMENSIONS = (1280, 720)
    SCALE_LIMITS = (0.18, 1.90)
    RESIZE_DELAY = 80
    GLOBAL_SCALE_FACTOR = 0.55
    HEADER_SIZE_MULTIPLIER = 1.18
    SIDEBAR_WEIGHT = 24
    DETAIL_WEIGHT = 76

    # File and directory paths
    BASE_DIR = Path(__file__).resolve().parent.parent
    QUESTIONS_FILE = BASE_DIR / "datos" / "preguntas.json"
    IMAGES_DIR = BASE_DIR / "recursos" / "imagenes"
    AUDIO_DIR = BASE_DIR / "recursos" / "audio"

    # Icon filenames
    ICONS = {"audio": "volume.svg", "search": "search.svg", "back": "arrow.svg"}

    # UI Colors
    COLORS = {
        "header_bg": "#1C2534",
        "header_hover": "#273246",
        "primary": "#1D6CFF",
        "primary_hover": "#0F55C9",
        "secondary": "#00CFC5",
        "secondary_hover": "#04AFA6",
        "danger": "#FF4F60",
        "danger_hover": "#E53949",
        "success": "#047857",
        "bg_light": "#F5F7FA",
        "bg_white": "#FFFFFF",
        "bg_modal": "#202632",
        "border_light": "#D2DAE6",
        "border_medium": "#CBD5E1",
        "search_bg": "#D1D8E0",
        "text_dark": "#111827",
        "text_medium": "#1F2937",
        "text_light": "#4B5563",
        "text_lighter": "#6B7280",
        "text_white": "#FFFFFF",
        "text_placeholder": "#F5F7FA",
        "text_error": "#DC2626",
        "btn_cancel": "#E5E7EB",
        "btn_cancel_hover": "#CBD5E1",
        "question_bg": "transparent",
        "question_text": "#1F2937",
        "question_hover": "#E2E8F0",
        "question_selected": "#1D6CFF",
    }

    # UI Sizes
    SIZES = {
        "max_questions": 8,
        "detail_image": (220, 220),
        "audio_icon": (32, 32),
        "search_icon": (16, 16),
        "back_icon": (20, 20),
        "question_btn_height": 50,
        "question_margin": 8,
        "question_padding": 4,
        "question_corner_radius": 12,
    }

    DEFINITION_PADDING_PROFILE = [
        (360, 8),
        (480, 10),
        (640, 12),
        (800, 14),
        (1024, 16),
        (1280, 18),
        (1600, 20),
        (1920, 22),
        (2560, 24),
        (3200, 26),
        (3840, 28),
    ]

    DEFINITION_WRAP_FILL_PROFILE = [
        (360, 0.90),
        (480, 0.92),
        (640, 0.94),
        (800, 0.95),
        (1024, 0.96),
        (1280, 0.955),
        (1600, 0.945),
        (1920, 0.940),
        (2560, 0.935),
        (3200, 0.930),
        (3840, 0.925),
    ]

    DEFINITION_WRAP_PIXEL_PROFILE = [
        (360, 320),
        (480, 420),
        (640, 560),
        (800, 720),
        (1024, 900),
        (1280, 1100),
        (1600, 1300),
        (1920, 1500),
        (2560, 1800),
        (3200, 2050),
        (3840, 2200),
    ]

    DEFINITION_WRAP_LIMITS = (240, 2200)
    DEFINITION_STACK_BREAKPOINT = 520
    VIEWPORT_WRAP_RATIO_PROFILE = [
        (360, 0.75),
        (3840, 0.75),
    ]

    SIDEBAR_WIDTH_PROFILE = [
        (720, 0.26),
        (960, 0.27),
        (1280, 0.28),
        (1440, 0.29),
        (1600, 0.30),
        (1920, 0.30),
        (2560, 0.31),
        (3200, 0.31),
        (3840, 0.32),
    ]

    LOW_RES_SCALE_PROFILE = [
        (360, 0.62),
        (480, 0.72),
        (600, 0.82),
        (720, 1.00),
    ]

    FONT_SPECS = {
        "title": ("Poppins ExtraBold", 44, "bold", 16),
        "body": ("Poppins Medium", 18, None, 9),
        "button": ("Poppins SemiBold", 16, "bold", 9),
        "header_button": ("Poppins SemiBold", 22, "bold", 12),
        "cancel_button": ("Poppins ExtraBold", 16, "bold", 9),
        "search": ("Poppins SemiBold", 18, "bold", 9),
        "question": ("Poppins SemiBold", 18, "bold", 9),
        "detail_title": ("Poppins ExtraBold", 38, "bold", 12),
        "dialog_title": ("Poppins SemiBold", 24, "bold", 12),
        "dialog_body": ("Poppins Medium", 16, None, 9),
        "dialog_label": ("Poppins SemiBold", 16, "bold", 9),
    }

    def __init__(self, parent, on_return_callback=None):
        self.parent = parent
        self.on_return_callback = on_return_callback

        # Declare font attributes (set in init_fonts)
        self.title_font = None
        self.body_font = None
        self.button_font = None
        self.header_button_font = None
        self.cancel_button_font = None
        self.search_font = None
        self.question_font = None
        self.detail_title_font = None
        self.dialog_title_font = None
        self.dialog_body_font = None
        self.dialog_label_font = None

        self.font_base_sizes = {}
        self.font_min_sizes = {}

        # Initialize fonts
        self.init_fonts()

        # Initialize services
        self.tts = TTSService(self.AUDIO_DIR)
        self.image_handler = ImageHandler(self.IMAGES_DIR)
        self.repository = QuestionRepository(self.QUESTIONS_FILE)

        # Question management state
        self.questions = self.repository.questions
        self.filtered_questions = list(self.questions)

        # UI State
        self.current_question = (
            self.filtered_questions[0] if self.filtered_questions else None
        )
        self.selected_question_button = None
        self.detail_visible = False

        # UI Components (initialized in build_ui)
        self.search_entry = None
        self.list_container = None
        self.detail_container = None
        self.detail_title_label = None
        self.detail_definition_textbox = None
        self.detail_image_label = None
        self.definition_audio_button = None

        # Layout references
        self.main_frame = None
        self.header_frame = None
        self.menu_button = None
        self.header_title_label = None
        self.sidebar_frame = None
        self.controls_frame = None
        self.search_wrapper = None
        self.search_icon_label = None
        self.add_button = None
        self.list_frame_padding = 8
        self.list_frame_corner_radius = 24
        self.detail_header_frame = None
        self.detail_body_frame = None
        self.detail_content_frame = None
        self.definition_row = None
        self.detail_action_buttons = []
        self.divider_frame = None
        self.current_detail_image = None
        self.render_metric_snapshot = None
        self.detail_scroll_height = 0
        self.definition_pad = 0
        self.definition_button_width = 0
        self.definition_button_gap = 16
        self.definition_layout_inline = True
        self.header_pad = 0
        self.body_pad = 0
        self.current_window_width = self.BASE_DIMENSIONS[0]
        self.current_window_height = self.BASE_DIMENSIONS[1]

        # Modal state
        self.current_modal = None

        # Cache icons
        self.detail_image_placeholder = (
            self.image_handler.create_transparent_placeholder()
        )
        self.audio_icon = self.image_handler.create_ctk_icon(
            self.ICONS["audio"], self.SIZES["audio_icon"]
        )
        self.search_icon = self.image_handler.create_ctk_icon(
            self.ICONS["search"], self.SIZES["search_icon"]
        )
        self.back_arrow_icon = self.image_handler.create_ctk_icon(
            self.ICONS["back"], self.SIZES["back_icon"]
        )

        self.icon_base_sizes = {
            "audio": self.SIZES["audio_icon"],
            "search": self.SIZES["search_icon"],
            "back": self.SIZES["back_icon"],
        }
        self.icon_cache = {}

        self.size_state = dict(self.SIZES)
        self.current_scale = 1.0
        self._resize_job = None

        # Clear parent and build UI
        for widget in self.parent.winfo_children():
            widget.destroy()
        self.build_ui()

        self.apply_responsive()

        # Bind click event to remove focus from search when clicking elsewhere
        self.parent.bind("<Button-1>", self.handle_global_click, add="+")
        self.parent.bind("<Configure>", self.on_resize)

    def init_fonts(self):
        for name, (family, size, weight, min_size) in self.FONT_SPECS.items():
            font = (
                ctk.CTkFont(family=family, size=size, weight=weight)
                if weight
                else ctk.CTkFont(family=family, size=size)
            )
            setattr(self, f"{name}_font", font)
            self.font_base_sizes[name] = size
            self.font_min_sizes[name] = min_size or 10

    def create_modal_ui_config(self, keys):
        color_map = {
            "BG_LIGHT": "bg_light",
            "BG_WHITE": "bg_white",
            "BG_MODAL_HEADER": "bg_modal",
            "BORDER_MEDIUM": "border_medium",
            "PRIMARY_BLUE": "primary",
            "PRIMARY_BLUE_HOVER": "primary_hover",
            "BUTTON_CANCEL_BG": "btn_cancel",
            "BUTTON_CANCEL_HOVER": "btn_cancel_hover",
            "TEXT_DARK": "text_dark",
            "TEXT_WHITE": "text_white",
            "TEXT_LIGHT": "text_light",
            "TEXT_ERROR": "text_error",
            "SUCCESS_GREEN": "success",
            "DANGER_RED": "danger",
            "DANGER_RED_HOVER": "danger_hover",
        }

        config_dict = {k: self.COLORS[v] for k, v in color_map.items() if k in keys}

        font_keys = [
            "dialog_title_font",
            "dialog_label_font",
            "dialog_body_font",
            "body_font",
            "button_font",
            "cancel_button_font",
        ]
        config_dict.update({k: getattr(self, k) for k in font_keys if k in keys})

        return SimpleNamespace(**config_dict)

    def show_save_error(self, error):
        message = (
            "Unable to update the questions file. "
            f"Please check permissions and try again.\n\nDetails: {error}"
        )
        try:
            messagebox.showerror("Save error", message)
        except tk.TclError:
            print(f"Save error: {message}")

    def filter_questions(self, query):
        query = (query or "").strip().lower()
        self.filtered_questions = (
            [q for q in self.questions if query in q.get("title", "").lower()]
            if query
            else list(self.questions)
        )

    def build_ui(self):
        self.parent.grid_rowconfigure(0, weight=1)
        self.parent.grid_columnconfigure(0, weight=1)

        self.main_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.grid_rowconfigure(1, weight=1)
        column_layout = {
            0: {"weight": self.SIDEBAR_WEIGHT, "minsize": 280},
            1: {"weight": 0, "minsize": 2},
            2: {"weight": self.DETAIL_WEIGHT, "minsize": 220},
        }
        for col, cfg in column_layout.items():
            self.main_frame.grid_columnconfigure(col, **cfg)

        self.build_header(self.main_frame)
        self.build_detail_panel(self.main_frame)
        self.build_sidebar(self.main_frame)
        self.build_divider(self.main_frame)

    def build_header(self, parent):
        c = self.COLORS
        self.header_frame = ctk.CTkFrame(
            parent, fg_color=c["header_bg"], corner_radius=0
        )
        self.header_frame.grid(row=0, column=0, columnspan=3, sticky="ew")
        self.header_frame.grid_columnconfigure(1, weight=1)

        self.menu_button = ctk.CTkButton(
            self.header_frame,
            text="Menu",
            font=self.header_button_font or self.button_font,
            text_color=c["text_white"],
            image=self.back_arrow_icon,
            compound="left",
            anchor="w",
            fg_color="transparent",
            hover_color=c["header_hover"],
            command=self.return_to_menu,
            corner_radius=8,
            width=110,
            height=44,
        )
        self.menu_button.grid(row=0, column=0, padx=(24, 16), pady=(28, 32), sticky="w")

        self.header_title_label = ctk.CTkLabel(
            self.header_frame,
            text="Manage Questions",
            font=self.title_font,
            text_color=c["text_white"],
            anchor="center",
        )
        self.header_title_label.grid(
            row=0, column=1, padx=32, pady=(28, 32), sticky="nsew"
        )

    def build_sidebar(self, parent):
        self.sidebar_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.sidebar_frame.grid(row=1, column=0, sticky="nsew", padx=(32, 12), pady=32)
        self.sidebar_frame.grid_rowconfigure(1, weight=1)
        self.sidebar_frame.grid_columnconfigure(0, weight=1)

        self.build_controls(self.sidebar_frame)
        self.build_question_list_container(self.sidebar_frame)

    def build_controls(self, parent):
        c = self.COLORS
        self.controls_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.controls_frame.grid(row=0, column=0, sticky="ew")
        self.controls_frame.grid_columnconfigure(0, weight=1)

        # Search bar
        self.search_wrapper = ctk.CTkFrame(
            self.controls_frame, fg_color=c["search_bg"], corner_radius=18
        )
        self.search_wrapper.grid(row=0, column=0, padx=(16, 12), pady=16, sticky="ew")
        self.search_wrapper.grid_columnconfigure(1, weight=1)

        # Search icon
        icon_config = {
            "text": "",
            "image": self.search_icon,
            "fg_color": "transparent",
            "width": 32,
        }
        if not self.search_icon:
            icon_config.update(
                {"text": "S", "text_color": c["text_white"], "font": self.button_font}
            )

        self.search_icon_label = ctk.CTkLabel(self.search_wrapper, **icon_config)
        self.search_icon_label.grid(row=0, column=0, padx=(12, 4), sticky="w")

        # Search entry
        self.search_entry = ctk.CTkEntry(
            self.search_wrapper,
            placeholder_text="Search...",
            placeholder_text_color=c["text_placeholder"],
            fg_color="transparent",
            text_color=c["text_white"],
            font=self.search_font,
            corner_radius=0,
            height=42,
            border_width=0,
        )
        self.search_entry.grid(row=0, column=1, padx=(4, 18), pady=4, sticky="nsew")
        for event in ("<KeyRelease>", "<<Paste>>", "<<Cut>>"):
            self.search_entry.bind(event, lambda e: self.handle_search())

        # Add button
        self.add_button = ctk.CTkButton(
            self.controls_frame,
            text="Add",
            font=self.button_font,
            fg_color=c["primary"],
            hover_color=c["primary_hover"],
            command=self.on_add_clicked,
            width=96,
            height=42,
            corner_radius=12,
        )
        self.add_button.grid(row=0, column=1, padx=(0, 16), pady=16)

    def build_question_list_container(self, parent):
        self.list_container = ctk.CTkFrame(parent, fg_color="transparent")
        self.list_container.grid(row=1, column=0, sticky="nsew", pady=(20, 0))
        self.list_container.grid_columnconfigure(0, weight=1)
        self.list_container.grid_rowconfigure(0, weight=1)

        self.render_question_list()

    def build_divider(self, parent):
        self.divider_frame = ctk.CTkFrame(
            parent,
            fg_color=self.COLORS["border_light"],
            corner_radius=0,
            width=2,
        )
        self.divider_frame.grid(row=1, column=1, sticky="ns", pady=32)

    def build_detail_panel(self, parent):
        c = self.COLORS
        self.detail_container = ctk.CTkFrame(
            parent,
            fg_color=c["bg_light"],
            corner_radius=16,
            border_width=1,
            border_color=c["border_light"],
        )
        self.detail_container.grid(
            row=1, column=2, sticky="nsew", padx=(12, 32), pady=32
        )
        self.detail_container.grid_rowconfigure(1, weight=1)
        self.detail_container.grid_columnconfigure(0, weight=1)

        self.build_detail_header()
        self.build_detail_body()

        # Hide initially
        self.detail_container.grid_remove()
        self.detail_visible = False

    def build_detail_header(self):
        c = self.COLORS
        self.detail_header_frame = ctk.CTkFrame(
            self.detail_container, fg_color="transparent"
        )
        self.detail_header_frame.grid(
            row=0, column=0, sticky="ew", padx=24, pady=(24, 12)
        )
        self.detail_header_frame.grid_columnconfigure(0, weight=1)

        self.detail_title_label = ctk.CTkLabel(
            self.detail_header_frame,
            text="",
            font=self.detail_title_font,
            text_color=c["text_dark"],
            anchor="w",
            wraplength=600,
        )
        self.detail_title_label.grid(row=0, column=0, sticky="w", padx=(12, 0))

        # Action buttons
        self.detail_action_buttons = []
        for col, (text, fg, hover, cmd) in enumerate(
            [
                ("Edit", c["secondary"], c["secondary_hover"], self.on_edit_clicked),
                ("Delete", c["danger"], c["danger_hover"], self.on_delete_clicked),
            ],
            start=1,
        ):
            button = ctk.CTkButton(
                self.detail_header_frame,
                text=text,
                font=self.question_font,
                fg_color=fg,
                hover_color=hover,
                command=cmd,
                width=110,
                height=44,
                corner_radius=12,
            )
            button.grid(row=0, column=col, padx=(12, 12 if col == 1 else 0), sticky="e")
            self.detail_action_buttons.append(button)

    def build_detail_body(self):
        c = self.COLORS
        self.detail_body_frame = ctk.CTkFrame(
            self.detail_container, fg_color="transparent"
        )
        self.detail_body_frame.grid(
            row=1, column=0, sticky="nsew", padx=24, pady=(0, 24)
        )
        self.detail_body_frame.grid_rowconfigure(0, weight=1)
        self.detail_body_frame.grid_columnconfigure(0, weight=1)

        self.detail_content_frame = ctk.CTkFrame(
            self.detail_body_frame, fg_color="transparent", height=520
        )
        self.detail_content_frame.grid(row=0, column=0, sticky="nsew")
        self.detail_content_frame.grid_columnconfigure(0, weight=1)
        self.detail_content_frame.grid_rowconfigure(1, weight=1)

        # Image label
        self.detail_image_label = ctk.CTkLabel(
            self.detail_content_frame,
            text="Image placeholder",
            font=self.search_font,
            text_color=c["text_light"],
            fg_color="transparent",
            width=220,
            height=220,
            anchor="center",
        )
        self.detail_image_label.grid(
            row=0, column=0, pady=(28, 48), padx=12, sticky="n"
        )

        try:
            self.detail_image_label.configure(image=self.detail_image_placeholder)
        except tk.TclError:
            pass

        # Definition row with audio button
        self.definition_row = ctk.CTkFrame(
            self.detail_content_frame, fg_color="transparent"
        )
        self.definition_row.grid(row=1, column=0, sticky="nsew", padx=32, pady=(32, 0))
        self.definition_row.grid_columnconfigure(1, weight=1)
        self.definition_row.grid_rowconfigure(0, weight=1)

        audio_config = {
            "text": "" if self.audio_icon else "Audio",
            "image": self.audio_icon,
            "fg_color": "transparent",
            "hover_color": "#E5E7EB",
            "command": self.on_audio_clicked,
            "state": "disabled",
            "width": 44,
            "height": 44,
            "corner_radius": 22,
        }
        if not self.audio_icon:
            audio_config.update(
                {"font": self.body_font, "text_color": c["text_medium"]}
            )

        self.definition_audio_button = ctk.CTkButton(
            self.definition_row, **audio_config
        )
        self.definition_audio_button.grid(row=0, column=0, sticky="nw", padx=(0, 16))

        self.detail_definition_textbox = ctk.CTkTextbox(
            self.definition_row,
            font=self.body_font,
            text_color=c["text_medium"],
            fg_color="transparent",
            wrap="word",
            height=100,
            activate_scrollbars=True,
            border_width=0,
        )
        self.detail_definition_textbox.grid(row=0, column=1, sticky="nsew")
        self.detail_definition_textbox.configure(state="disabled")

    def _create_list_frame_container(self, is_scrollable):
        """Create the outer and inner frames for the question list."""
        c = self.COLORS

        # Create outer frame for border and background
        outer_frame = ctk.CTkFrame(
            self.list_container,
            fg_color=c["bg_light"],
            border_width=1,
            border_color=c["border_light"],
            corner_radius=self.list_frame_corner_radius,
        )
        outer_frame.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=self.list_frame_padding,
            pady=self.list_frame_padding,
        )
        outer_frame.grid_columnconfigure(0, weight=1)
        outer_frame.grid_rowconfigure(0, weight=1)

        # Create inner list frame (transparent)
        frame_config = {
            "fg_color": "transparent",
            "border_width": 0,
            "corner_radius": 0,
        }
        FrameClass = ctk.CTkScrollableFrame if is_scrollable else ctk.CTkFrame
        list_frame = FrameClass(outer_frame, **frame_config)

        # Add padding to keep content/scrollbar away from the outer border
        inner_padding = 4
        list_frame.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=inner_padding,
            pady=inner_padding,
        )
        list_frame.grid_columnconfigure(0, weight=1)
        inner_frame = getattr(list_frame, "_scrollable_frame", None)
        if inner_frame:
            try:
                inner_frame.grid_columnconfigure(0, weight=1)
            except tk.TclError:
                pass

        return list_frame

    def _show_empty_list_state(self, list_frame, has_search_query):
        """Display empty state message when no questions are available."""
        c = self.COLORS
        empty_text = (
            "No questions match your search."
            if has_search_query
            else "No questions available."
        )
        ctk.CTkLabel(
            list_frame,
            text=empty_text,
            font=self.body_font,
            text_color=c["text_lighter"],
        ).grid(row=1, column=0, padx=24, pady=(12, 24))

    def _create_question_button(self, parent, question, is_selected, button_config):
        """Create a single question button with appropriate styling."""
        c = self.COLORS
        button = ctk.CTkButton(
            parent,
            text=question.get("title", ""),
            font=self.question_font,
            text_color=c["text_white"] if is_selected else c["question_text"],
            fg_color=c["question_selected"] if is_selected else c["question_bg"],
            hover_color=(
                c["question_selected"] if is_selected else c["question_hover"]
            ),
            border_width=0,
            **button_config,
        )

        # Configure command to properly capture references
        button.configure(
            command=lambda q=question, b=button: self.on_question_selected(q, b)
        )
        return button

    def render_question_list(self):
        """Render the list of questions with buttons."""
        if not self.list_container or not self.list_container.winfo_exists():
            return

        # Clear existing widgets
        for child in self.list_container.winfo_children():
            child.destroy()

        s = self.size_state
        questions = self.filtered_questions
        search_query = self.search_entry.get() if self.search_entry else ""

        # Check if selected question is visible
        selected_visible = (
            self.current_question in questions if self.current_question else False
        )
        if not selected_visible and self.current_question:
            self.clear_detail_panel()

        # Create container frames
        is_scrollable = len(questions) > s.get(
            "max_questions", self.SIZES["max_questions"]
        )
        list_frame = self._create_list_frame_container(is_scrollable)

        # Show empty state if no questions
        if not questions:
            self._show_empty_list_state(list_frame, search_query.strip())
            return

        # Prepare button configuration
        button_config = {
            "height": s.get("question_btn_height", self.SIZES["question_btn_height"]),
            "corner_radius": s.get(
                "question_corner_radius", self.SIZES["question_corner_radius"]
            ),
        }
        button_margin = s.get("question_margin", self.SIZES["question_margin"])
        button_padding = s.get("question_padding", self.SIZES["question_padding"])

        # Render question buttons
        self.selected_question_button = None
        first_button = None

        for index, question in enumerate(questions, start=0):
            is_selected = selected_visible and question is self.current_question

            # Create button
            button = self._create_question_button(
                list_frame, question, is_selected, button_config
            )

            # Adjust padding for scrollbar if needed
            btn_padx = button_margin
            if is_scrollable:
                offset = s.get("scrollbar_offset_active", 22)
                btn_padx = (button_margin, button_margin + offset)

            button.grid(
                row=index,
                column=0,
                sticky="nsew",
                padx=btn_padx,
                pady=button_padding,
            )

            if first_button is None:
                first_button = button

            if is_selected:
                self.selected_question_button = button

        # Auto-select first question if none selected
        if not self.current_question and first_button:
            self.on_question_selected(questions[0], first_button)
            return

        # Show detail panel for current selection
        if (
            self.current_question
            and self.selected_question_button
            and not self.detail_visible
        ):
            self.on_question_selected(
                self.current_question, self.selected_question_button
            )

    def handle_search(self):
        query = self.search_entry.get() if self.search_entry else ""
        self.filter_questions(query)
        self.render_question_list()

    def handle_global_click(self, event):
        if not self.search_entry or not self.search_entry.winfo_exists():
            return

        # Check if the click was outside the search entry
        widget = event.widget

        # Check if clicked widget is the search entry or any parent widget chain
        current_widget = widget
        is_search_entry = False

        # Walk up the widget hierarchy to check if search_entry is an ancestor
        while current_widget:
            if current_widget == self.search_entry:
                is_search_entry = True
                break
            try:
                current_widget = current_widget.master
            except (AttributeError, tk.TclError):
                break

        # If not clicked on search entry or its children, remove focus
        if not is_search_entry:
            self.parent.focus_set()

    def on_question_selected(self, question, button):
        self.tts.stop()

        # Show detail panel if hidden
        if not self.detail_visible:
            self.detail_container.grid()
            self.detail_visible = True

        c = self.COLORS
        # Update button selection
        if (
            self.selected_question_button
            and self.selected_question_button is not button
            and self.selected_question_button.winfo_exists()
        ):
            try:
                self.selected_question_button.configure(
                    fg_color=c["question_bg"],
                    text_color=c["question_text"],
                    hover_color=c["question_hover"],
                )
            except tk.TclError:
                pass

        button.configure(
            fg_color=c["question_selected"],
            text_color=c["text_white"],
            hover_color=c["question_selected"],
        )
        self.selected_question_button = button

        # Update detail content
        self.current_question = question
        title = question.get("title", "")
        definition = (
            question.get("definition", "").strip() or "No definition available yet."
        )
        image_path = question.get("image", "")

        self.detail_title_label.configure(text=title)
        if (
            self.detail_definition_textbox
            and self.detail_definition_textbox.winfo_exists()
        ):
            self.detail_definition_textbox.configure(state="normal")
            self.detail_definition_textbox.delete("0.0", "end")
            self.detail_definition_textbox.insert("0.0", definition)
            self.detail_definition_textbox.configure(state="disabled")

        if self.detail_title_label and self.detail_title_label.winfo_exists():
            try:
                self.detail_title_label.after_idle(self.apply_title_wraplength)
            except tk.TclError:
                self.apply_title_wraplength()

        # Update image
        self.update_detail_image(image_path)

        # Enable/disable audio button
        self.definition_audio_button.configure(
            state="normal" if question.get("definition", "").strip() else "disabled"
        )

    def clear_detail_panel(self):
        self.tts.stop()
        self.current_question = None
        self.selected_question_button = None

        if (
            self.detail_visible
            and self.detail_container
            and self.detail_container.winfo_exists()
        ):
            self.detail_container.grid_remove()
            self.detail_visible = False

        self.current_detail_image = None

        # Reset widgets
        if self.detail_title_label and self.detail_title_label.winfo_exists():
            self.detail_title_label.configure(text="")
        if (
            self.detail_definition_textbox
            and self.detail_definition_textbox.winfo_exists()
        ):
            self.detail_definition_textbox.configure(state="normal")
            self.detail_definition_textbox.delete("0.0", "end")
            self.detail_definition_textbox.configure(state="disabled")
        if self.definition_audio_button and self.definition_audio_button.winfo_exists():
            self.definition_audio_button.configure(state="disabled")

        if self.detail_image_label and self.detail_image_label.winfo_exists():
            try:
                self.detail_image_label.configure(
                    image=self.detail_image_placeholder, text="Image placeholder"
                )
            except tk.TclError:
                pass

    def update_detail_image(self, image_path):
        if not self.detail_image_label or not self.detail_image_label.winfo_exists():
            return

        size = self.size_state.get("detail_image", self.SIZES["detail_image"])
        try:
            self.detail_image_placeholder.configure(size=size)
        except tk.TclError:
            pass

        detail_image = (
            self.image_handler.create_detail_image(image_path, size)
            if image_path
            else None
        )
        self.current_detail_image = detail_image

        fallback_text = ""
        if not detail_image:
            fallback_text = "Image not available" if image_path else "Image placeholder"

        try:
            self.detail_image_label.configure(
                image=detail_image or self.detail_image_placeholder, text=fallback_text
            )
        except tk.TclError:
            pass

    def refresh_detail_image(self):
        image_path = ""
        if self.current_question:
            image_path = self.current_question.get("image", "")
        self.update_detail_image(image_path)

    def measure_widget_width(self, widget, fallback):
        if widget and widget.winfo_exists():
            try:
                widget.update_idletasks()
            except tk.TclError:
                pass
            width = widget.winfo_width()
            if width > 1:
                return width
        return fallback

    def get_effective_detail_width(self):
        fallback = self.size_state.get(
            "detail_width_estimate", self.BASE_DIMENSIONS[0] // 2
        )
        return self.measure_widget_width(
            getattr(self, "detail_body_frame", None), fallback
        )

    def get_detail_viewport_width(self):
        content = getattr(self, "detail_content_frame", None)
        fallback = self.size_state.get(
            "detail_width_estimate", self.BASE_DIMENSIONS[0] // 2
        )
        if not content or not content.winfo_exists():
            return fallback

        canvas = getattr(content, "_parent_canvas", None)
        if canvas and canvas.winfo_exists():
            try:
                canvas.update_idletasks()
            except tk.TclError:
                pass
            width = canvas.winfo_width()
            if width > 1:
                return width

        return self.measure_widget_width(content, fallback)

    def get_visible_detail_width(self):
        window_width = max(
            getattr(self, "current_window_width", self.BASE_DIMENSIONS[0]), 200
        )
        sidebar_fallback = self.size_state.get(
            "sidebar_width_estimate", window_width // 3
        )
        sidebar_width = self.measure_widget_width(
            getattr(self, "sidebar_frame", None), sidebar_fallback
        )
        divider_width = self.measure_widget_width(
            getattr(self, "divider_frame", None), 2
        )
        outer_margin = self.scale_value(72, self.current_scale or 1, 40, 140)
        visible_width = window_width - sidebar_width - divider_width - outer_margin
        return max(120, visible_width)

    def interpolate_profile(self, value, profile):
        # Map actual widths into tuned spacing/wrap values using linear segments
        if not profile:
            return value
        if value is None:
            value = profile[-1][0]
        sample_value = profile[0][1]

        def cast(result):
            if isinstance(sample_value, float):
                return float(result)
            return int(round(result))

        lower_bound, lower_value = profile[0]
        if value <= lower_bound:
            return cast(lower_value)
        for upper_bound, upper_value in profile[1:]:
            if value <= upper_bound:
                span = upper_bound - lower_bound or 1
                ratio = (value - lower_bound) / span
                interpolated = lower_value + ratio * (upper_value - lower_value)
                return cast(interpolated)
            lower_bound, lower_value = upper_bound, upper_value
        return cast(profile[-1][1])

    def clamp_value(self, value, min_value=None, max_value=None):
        if min_value is not None:
            value = max(min_value, value)
        if max_value is not None:
            value = min(max_value, value)
        return value

    def get_wrap_ratio(self, width=None):
        target_width = (
            width if width is not None else self.size_state.get("detail_width_estimate")
        )
        if not target_width:
            target_width = self.BASE_DIMENSIONS[0] * 0.6
        ratio = self.interpolate_profile(
            target_width, self.DEFINITION_WRAP_FILL_PROFILE
        )
        return self.clamp_value(ratio, 0.78, 0.985)

    def compute_definition_padding(self, width=None):
        target_width = width if width is not None else self.get_effective_detail_width()
        pad = self.interpolate_profile(target_width, self.DEFINITION_PADDING_PROFILE)
        min_pad = self.scale_value(8, self.current_scale or 1, 6, 16)
        max_pad = self.scale_value(36, self.current_scale or 1, 24, 60)
        small_width = target_width <= 640
        if small_width:
            pad *= 0.7
            pad = max(6, pad)
        return self.clamp_value(pad, min_pad, max_pad)

    def get_sidebar_share(self, window_width):
        if not window_width or window_width <= 0:
            window_width = self.BASE_DIMENSIONS[0]
        profile_share = self.interpolate_profile(
            window_width, self.SIDEBAR_WIDTH_PROFILE
        )
        total_weight = self.SIDEBAR_WEIGHT + self.DETAIL_WEIGHT
        base_share = self.SIDEBAR_WEIGHT / total_weight if total_weight else 0.26
        return self.clamp_value(profile_share, base_share, 0.32)

    def apply_title_wraplength(self):
        if not self.detail_title_label or not self.detail_title_label.winfo_exists():
            return
        fallback = self.size_state.get("detail_width_estimate", 600)
        width = self.measure_widget_width(self.detail_header_frame, fallback)
        width -= max(40, self.header_pad or 0)
        wrap_target = max(120, width)
        self.detail_title_label.configure(wraplength=wrap_target)

    def scale_value(self, base, scale, min_value=None, max_value=None):
        value = base * scale
        if min_value is not None:
            value = max(min_value, value)
        if max_value is not None:
            value = min(max_value, value)
        return int(round(value))

    def header_value(self, value):
        return value * self.HEADER_SIZE_MULTIPLIER

    def update_size_state(self, scale, window_width):
        self.size_state["question_btn_height"] = self.scale_value(50, scale, 26, 86)
        self.size_state["question_margin"] = self.scale_value(8, scale, 3, 18)
        self.size_state["question_padding"] = self.scale_value(4, scale, 2, 14)
        self.size_state["question_corner_radius"] = self.scale_value(12, scale, 5, 20)
        self.size_state["max_questions"] = max(
            4, min(12, int(round(self.SIZES["max_questions"] * scale)))
        )

        detail_size = (
            self.scale_value(220, scale, 110, 420),
            self.scale_value(220, scale, 110, 420),
        )
        self.size_state["detail_image"] = detail_size
        panel_height = self.scale_value(520, scale, 320, 880)
        scroll_height = max(200, panel_height - self.scale_value(150, scale, 90, 260))
        self.size_state["detail_panel_height"] = panel_height
        self.size_state["detail_scroll_height"] = scroll_height

        self.list_frame_padding = self.scale_value(8, scale, 4, 24)
        self.list_frame_corner_radius = self.scale_value(24, scale, 12, 40)

        sidebar_base = 280
        detail_base = 820
        sidebar_minsize = self.scale_value(sidebar_base, scale, 220, 560)
        raw_detail_min = self.scale_value(detail_base, scale, 320, 1400)
        gutter = self.scale_value(60, scale, 32, 110)
        estimated_sidebar_width = max(
            sidebar_minsize,
            int(round(window_width * self.get_sidebar_share(window_width))),
        )
        available_width = max(220, window_width - estimated_sidebar_width - gutter)
        detail_minsize = min(raw_detail_min, available_width)
        estimated_detail_width = max(detail_minsize, available_width)
        scrollbar_offset = self.scale_value(22, scale, 12, 36)
        self.size_state["scrollbar_offset_base"] = scrollbar_offset
        self.size_state["scrollbar_offset_active"] = scrollbar_offset

        if self.main_frame and self.main_frame.winfo_exists():
            self.main_frame.grid_columnconfigure(0, minsize=sidebar_minsize)
            self.main_frame.grid_columnconfigure(2, minsize=detail_minsize)
        self.size_state["detail_width_estimate"] = estimated_detail_width
        self.size_state["window_width"] = window_width
        self.size_state["sidebar_width_estimate"] = estimated_sidebar_width
        pad_estimate = self.compute_definition_padding(estimated_detail_width)
        self.size_state["definition_pad_estimate"] = pad_estimate * 2

    def update_fonts(self, scale):
        for name, base_size in self.font_base_sizes.items():
            font = getattr(self, f"{name}_font", None)
            if not font:
                continue
            min_size = self.font_min_sizes.get(name, 10)
            max_size = base_size * 2.2
            font.configure(size=self.scale_value(base_size, scale, min_size, max_size))

    def refresh_icons(self, scale):
        limits = {
            "audio": (18, 64),
            "search": (12, 32),
            "back": (16, 40),
        }
        for key, base_size in self.icon_base_sizes.items():
            min_limit, max_limit = limits.get(key, (12, 48))
            size = (
                self.scale_value(base_size[0], scale, min_limit, max_limit),
                self.scale_value(base_size[1], scale, min_limit, max_limit),
            )
            cached = self.icon_cache.get(key)
            if cached and cached["size"] == size:
                image = cached["image"]
            else:
                image = self.image_handler.create_ctk_icon(self.ICONS[key], size)
                self.icon_cache[key] = {"size": size, "image": image}

            if key == "audio":
                self.audio_icon = image
                if (
                    self.definition_audio_button
                    and self.definition_audio_button.winfo_exists()
                ):
                    if image:
                        self.definition_audio_button.configure(image=image, text="")
                    else:
                        self.definition_audio_button.configure(image=None, text="Audio")
            elif key == "search":
                self.search_icon = image
                if self.search_icon_label and self.search_icon_label.winfo_exists():
                    if image:
                        self.search_icon_label.configure(
                            image=image, text="", width=size[0]
                        )
                    else:
                        self.search_icon_label.configure(
                            image=None,
                            text="S",
                            font=self.button_font,
                            text_color=self.COLORS["text_white"],
                        )
            elif key == "back":
                self.back_arrow_icon = image
                if self.menu_button and self.menu_button.winfo_exists():
                    self.menu_button.configure(image=image)

    def update_header_layout(self, scale):
        if not self.menu_button or not self.menu_button.winfo_exists():
            return

        header_val = self.header_value
        pad_top = self.scale_value(
            header_val(24), scale, header_val(12), header_val(64)
        )
        pad_bottom = self.scale_value(
            header_val(30), scale, header_val(14), header_val(72)
        )
        pad_left = self.scale_value(
            header_val(28), scale, header_val(10), header_val(84)
        )
        pad_right = self.scale_value(
            header_val(20), scale, header_val(8), header_val(56)
        )

        self.menu_button.grid_configure(
            padx=(pad_left, pad_right), pady=(pad_top, pad_bottom)
        )
        self.menu_button.configure(
            width=self.scale_value(
                header_val(130), scale, header_val(80), header_val(280)
            ),
            height=self.scale_value(
                header_val(48), scale, header_val(32), header_val(96)
            ),
            corner_radius=self.scale_value(
                header_val(12), scale, header_val(6), header_val(28)
            ),
        )

        if self.header_title_label and self.header_title_label.winfo_exists():
            self.header_title_label.grid_configure(
                padx=self.scale_value(
                    header_val(40), scale, header_val(14), header_val(96)
                ),
                pady=(pad_top, pad_bottom),
            )

        if self.divider_frame and self.divider_frame.winfo_exists():
            self.divider_frame.grid_configure(pady=self.scale_value(32, scale, 12, 72))
            self.divider_frame.configure(width=self.scale_value(2, scale, 1, 4))

    def update_sidebar_layout(self, scale):
        if not self.sidebar_frame or not self.sidebar_frame.winfo_exists():
            return

        pad_left = self.scale_value(28, scale, 10, 60)
        pad_right = self.scale_value(10, scale, 6, 40)
        pad_vertical = self.scale_value(32, scale, 12, 76)

        self.sidebar_frame.grid_configure(padx=(pad_left, pad_right), pady=pad_vertical)

        search_padx_left = self.scale_value(14, scale, 6, 32)
        search_padx_right = self.scale_value(10, scale, 6, 28)
        search_pady = self.scale_value(16, scale, 6, 36)
        if self.search_wrapper and self.search_wrapper.winfo_exists():
            self.search_wrapper.grid_configure(
                padx=(search_padx_left, search_padx_right), pady=search_pady
            )
            self.search_wrapper.configure(
                corner_radius=self.scale_value(18, scale, 10, 32)
            )

        if self.search_entry and self.search_entry.winfo_exists():
            self.search_entry.grid_configure(
                padx=(
                    self.scale_value(4, scale, 2, 18),
                    self.scale_value(18, scale, 8, 32),
                ),
                pady=self.scale_value(4, scale, 2, 18),
            )
            self.search_entry.configure(height=self.scale_value(42, scale, 28, 66))

        if self.search_icon_label and self.search_icon_label.winfo_exists():
            self.search_icon_label.grid_configure(
                padx=(
                    self.scale_value(12, scale, 6, 24),
                    self.scale_value(4, scale, 2, 16),
                )
            )

        if self.add_button and self.add_button.winfo_exists():
            self.add_button.grid_configure(
                padx=(
                    self.scale_value(0, scale, 0, 8),
                    self.scale_value(16, scale, 8, 36),
                ),
                pady=search_pady,
            )
            self.add_button.configure(
                width=self.scale_value(96, scale, 72, 200),
                height=self.scale_value(42, scale, 30, 72),
                corner_radius=self.scale_value(12, scale, 8, 24),
            )

        self.update_list_container_layout(scale)

    def update_list_container_layout(self, scale):
        if not self.list_container or not self.list_container.winfo_exists():
            return
        pad_y = self.scale_value(20, scale, 8, 40)
        self.list_container.grid_configure(padx=(0, 0), pady=(pad_y, 0))

    def update_detail_layout(self, scale):
        if not self.detail_container or not self.detail_container.winfo_exists():
            return

        detail_width = self.get_effective_detail_width()
        base_pad_left = 12
        base_pad_right = 32
        pad_left = self.scale_value(base_pad_left, scale, 6, 40)
        pad_right = self.scale_value(base_pad_right, scale, 12, 70)
        pad_vertical = self.scale_value(32, scale, 12, 76)

        self.detail_container.grid_configure(
            padx=(pad_left, pad_right), pady=pad_vertical
        )
        self.detail_container.configure(
            corner_radius=self.scale_value(16, scale, 10, 32)
        )
        panel_height = self.size_state.get("detail_panel_height", 520)
        scroll_height = self.size_state.get(
            "detail_scroll_height", max(180, panel_height - 140)
        )
        self.detail_container.grid_rowconfigure(1, minsize=panel_height)

        body_padx = self.scale_value(24, scale, 12, 56)
        if detail_width <= 640:
            body_padx = max(8, int(round(body_padx * 0.5)))
        body_pady = self.scale_value(24, scale, 12, 64)
        if self.detail_body_frame and self.detail_body_frame.winfo_exists():
            self.detail_body_frame.grid_configure(padx=body_padx, pady=(0, body_pady))
            self.detail_body_frame.configure(height=panel_height)
            self.body_pad = body_padx * 2

        image_pad_top = self.scale_value(28, scale, 12, 56)
        image_pad_bottom = self.scale_value(48, scale, 16, 96)
        image_padx = self.scale_value(12, scale, 6, 32)

        if self.detail_content_frame and self.detail_content_frame.winfo_exists():
            self.detail_content_frame.configure(height=scroll_height)

        header_padx = self.scale_value(24, scale, 12, 56)
        if self.detail_header_frame and self.detail_header_frame.winfo_exists():
            self.detail_header_frame.grid_configure(padx=header_padx)
            self.header_pad = header_padx * 2

        if self.detail_image_label and self.detail_image_label.winfo_exists():
            width, height = self.size_state.get(
                "detail_image", self.SIZES["detail_image"]
            )
            self.detail_image_label.grid_configure(
                pady=(image_pad_top, image_pad_bottom), padx=image_padx
            )
            self.detail_image_label.configure(width=width, height=height)

        if self.definition_row and self.definition_row.winfo_exists():
            definition_pad = self.compute_definition_padding(detail_width)
            if detail_width <= 640:
                definition_pad = max(4, int(round(definition_pad * 0.55)))
            self.definition_row.grid_configure(
                padx=definition_pad,
                pady=(self.scale_value(32, scale, 12, 60), 0),
            )
            self.definition_pad = definition_pad * 2

        if self.definition_audio_button and self.definition_audio_button.winfo_exists():
            button_width = self.scale_value(44, scale, 30, 76)
            button_gap = self.scale_value(16, scale, 10, 26)
            self.definition_audio_button.configure(
                width=button_width,
                height=self.scale_value(44, scale, 30, 76),
                corner_radius=self.scale_value(22, scale, 14, 40),
            )
            self.definition_audio_button.grid_configure(padx=(0, button_gap))
            self.definition_button_gap = button_gap
            self.definition_button_width = button_width + button_gap

        self.update_definition_audio_layout(detail_width, scale)

        for button in self.detail_action_buttons:
            if button and button.winfo_exists():
                button.configure(
                    width=self.scale_value(110, scale, 80, 240),
                    height=self.scale_value(44, scale, 30, 80),
                    corner_radius=self.scale_value(12, scale, 8, 24),
                )

        self.refresh_detail_image()
        if self.parent and self.parent.winfo_exists():
            try:
                self.parent.after_idle(self.apply_title_wraplength)
            except tk.TclError:
                self.apply_title_wraplength()

        if self.detail_title_label and self.detail_title_label.winfo_exists():
            # Set fixed height for title to prevent bouncing (approx 2 lines)
            base_size = self.font_base_sizes.get("detail_title", 38)
            min_size = self.font_min_sizes.get("detail_title", 12)
            max_size = base_size * 2.2
            current_font_size = self.scale_value(base_size, scale, min_size, max_size)
            title_height = int(current_font_size * 1.35 * 2)
            self.detail_title_label.configure(height=title_height)

    def update_definition_audio_layout(self, container_width, scale):
        if not self.definition_row or not self.definition_row.winfo_exists():
            return
        if not self.definition_audio_button or not self.detail_definition_textbox:
            return

        stack_threshold = self.scale_value(
            self.DEFINITION_STACK_BREAKPOINT, scale, 220, 640
        )
        should_stack = container_width <= stack_threshold
        target_inline = not should_stack
        if target_inline == self.definition_layout_inline:
            return

        self.definition_layout_inline = target_inline
        stack_gap = self.scale_value(10, scale, 6, 22)

        if should_stack:
            self.definition_row.grid_columnconfigure(0, weight=1)
            self.definition_row.grid_columnconfigure(1, weight=0)
            self.definition_audio_button.grid_configure(
                row=0,
                column=0,
                columnspan=2,
                sticky="w",
                pady=(0, stack_gap),
                padx=(0, 0),
            )
            self.detail_definition_textbox.grid_configure(
                row=1, column=0, columnspan=2, sticky="nsew"
            )
        else:
            self.definition_row.grid_columnconfigure(0, weight=0)
            self.definition_row.grid_columnconfigure(1, weight=1)
            self.definition_audio_button.grid_configure(
                row=0,
                column=0,
                columnspan=1,
                sticky="nw",
                pady=0,
                padx=(0, self.definition_button_gap),
            )
            self.detail_definition_textbox.grid_configure(
                row=0, column=1, columnspan=1, sticky="nsew"
            )

    def apply_responsive(self):
        if not self.parent or not self.parent.winfo_exists():
            return

        width = max(self.parent.winfo_width(), 1)
        height = max(self.parent.winfo_height(), 1)
        self.current_window_width = width
        self.current_window_height = height
        base_w, base_h = self.BASE_DIMENSIONS

        raw_scale = min(width / base_w, height / base_h)
        min_scale, max_scale = self.SCALE_LIMITS
        scaled = raw_scale * self.GLOBAL_SCALE_FACTOR
        if width <= 900:
            scaled *= 0.88
        if height <= 550:
            scaled *= 0.92
        min_dimension = min(width, height)
        extra_low_res_penalty = self.interpolate_profile(
            min_dimension, self.LOW_RES_SCALE_PROFILE
        )
        scaled *= extra_low_res_penalty
        scale = max(min_scale, min(max_scale, scaled))
        self.current_scale = scale

        self.update_size_state(scale, width)
        self.update_fonts(scale)
        self.refresh_icons(scale)
        self.update_header_layout(scale)
        self.update_sidebar_layout(scale)
        self.update_detail_layout(scale)

        metrics_snapshot = (
            self.size_state.get("question_btn_height"),
            self.size_state.get("question_margin"),
            self.size_state.get("question_padding"),
            self.size_state.get("question_corner_radius"),
            self.size_state.get("max_questions"),
            self.list_frame_padding,
            self.list_frame_corner_radius,
            self.size_state.get("detail_panel_height"),
            self.size_state.get("detail_scroll_height"),
        )
        needs_render = metrics_snapshot != self.render_metric_snapshot
        self.render_metric_snapshot = metrics_snapshot

        if needs_render:
            self.render_question_list()

        self.resize_current_modal()

        self._resize_job = None

    def resize_current_modal(self):
        if not self.current_modal:
            return

        root = None
        try:
            root = self.parent.winfo_toplevel()
        except tk.TclError:
            root = self.parent

        scale = None
        if hasattr(self.current_modal, "get_responsive_scale"):
            try:
                scale = self.current_modal.get_responsive_scale(root)
            except tk.TclError:
                scale = None

        if scale is None:
            return

        try:
            self.current_modal.resize(scale)
        except (AttributeError, tk.TclError):
            pass

    def on_resize(self, event):
        if event.widget is not self.parent:
            return
        if self._resize_job:
            try:
                self.parent.after_cancel(self._resize_job)
            except tk.TclError:
                pass
        self._resize_job = self.parent.after(self.RESIZE_DELAY, self.apply_responsive)

    def get_standard_modal_keys(self):
        return [
            "BG_LIGHT",
            "BG_WHITE",
            "BG_MODAL_HEADER",
            "BORDER_MEDIUM",
            "PRIMARY_BLUE",
            "PRIMARY_BLUE_HOVER",
            "BUTTON_CANCEL_BG",
            "BUTTON_CANCEL_HOVER",
            "TEXT_DARK",
            "TEXT_WHITE",
            "TEXT_LIGHT",
            "TEXT_ERROR",
            "SUCCESS_GREEN",
            "dialog_title_font",
            "dialog_label_font",
            "body_font",
            "button_font",
            "cancel_button_font",
        ]

    def on_add_clicked(self):
        ui_config = self.create_modal_ui_config(self.get_standard_modal_keys())
        self.current_modal = AddQuestionModal(
            self.parent, ui_config, self.image_handler, self.handle_add_save
        )
        self.current_modal.show()
        self.resize_current_modal()

    def handle_add_save(self, title, definition, source_image_path):
        if not self.repository.is_title_unique(title):
            messagebox.showwarning(
                "Duplicate Question",
                "A question with this title already exists. Please use a different title.",
            )
            return False  # Return False to prevent modal from closing

        # Copy image to project
        relative_image_path = self.image_handler.copy_image_to_project(
            source_image_path
        )
        if not relative_image_path:
            return False  # Error already shown, prevent modal from closing

        # Add question and update UI
        try:
            new_question = self.repository.add_question(
                title, definition, relative_image_path.as_posix()
            )
        except QuestionPersistenceError as error:
            self.show_save_error(error)
            return False

        self.filtered_questions = list(self.questions)
        self.current_question = new_question
        if self.search_entry:
            try:
                self.search_entry.delete(0, tk.END)
            except tk.TclError:
                pass
        self.render_question_list()
        # After render_question_list, selected_question_button is updated
        # Only call on_question_selected if button was found and set during render
        if self.selected_question_button:
            self.on_question_selected(new_question, self.selected_question_button)

        return True  # Success - allow modal to close

    def on_edit_clicked(self):
        if not self.current_question:
            return
        self.tts.stop()
        ui_config = self.create_modal_ui_config(self.get_standard_modal_keys())
        self.current_modal = EditQuestionModal(
            self.parent,
            ui_config,
            self.image_handler,
            self.handle_edit_save,
            question=self.current_question,
        )
        self.current_modal.show()
        self.resize_current_modal()

    def handle_edit_save(self, title, definition, image_path):
        if not self.repository.is_title_unique(
            title, exclude_question=self.current_question
        ):
            messagebox.showwarning(
                "Duplicate Question",
                "A question with this title already exists. Please use a different title.",
            )
            return False  # Return False to prevent modal from closing

        # Handle image path
        stored_image_path = image_path
        if hasattr(image_path, "as_posix"):
            relative_image_path = self.image_handler.copy_image_to_project(image_path)
            if not relative_image_path:
                return False  # Error already shown, prevent modal from closing
            stored_image_path = relative_image_path.as_posix()

        # Update question and UI
        try:
            updated_question = self.repository.update_question(
                self.current_question, title, definition, stored_image_path
            )
        except QuestionPersistenceError as error:
            self.show_save_error(error)
            return False

        self.current_question = updated_question
        self.handle_search()
        # After handle_search, selected_question_button is updated during render
        # Only call on_question_selected if button was found and set during render
        if self.selected_question_button:
            self.on_question_selected(updated_question, self.selected_question_button)

        return True  # Success - allow modal to close

    def on_delete_clicked(self):
        if not self.current_question:
            return
        self.tts.stop()

        delete_keys = [
            "BG_LIGHT",
            "BG_MODAL_HEADER",
            "DANGER_RED",
            "DANGER_RED_HOVER",
            "BUTTON_CANCEL_BG",
            "BUTTON_CANCEL_HOVER",
            "TEXT_DARK",
            "TEXT_WHITE",
            "dialog_title_font",
            "dialog_body_font",
            "button_font",
            "cancel_button_font",
        ]
        ui_config = self.create_modal_ui_config(delete_keys)
        self.current_modal = DeleteConfirmationModal(
            self.parent, ui_config, self.handle_delete_confirm
        )
        self.current_modal.show()
        self.resize_current_modal()

    def handle_delete_confirm(self):
        if not self.current_question:
            return

        try:
            deleted = self.repository.delete_question(self.current_question)
        except QuestionPersistenceError as error:
            self.show_save_error(error)
            return

        if deleted:
            self.clear_detail_panel()
            self.handle_search()

    def on_audio_clicked(self):
        if self.current_question:
            definition = self.current_question.get("definition", "").strip()
            if definition:
                self.tts.speak(definition)

    def return_to_menu(self):
        self.tts.stop()
        if self.on_return_callback:
            self.on_return_callback()

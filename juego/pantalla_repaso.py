import json
import tkinter as tk

import customtkinter as ctk
from PIL import Image

from juego.ayudantes_responsivos import ResponsiveScaler, get_logical_dimensions
from juego.manejador_imagenes import ImageHandler
from juego.pantalla_juego_config import (
    GAME_BASE_DIMENSIONS,
    GAME_BASE_SIZES,
    GAME_COLORS,
    GAME_FONT_SPECS,
    GAME_GLOBAL_SCALE_FACTOR,
    GAME_ICONS,
    GAME_PROFILES,
    GAME_RESIZE_DELAY,
    GAME_SCALE_LIMITS,
    GameFontRegistry,
    GameSizeCalculator,
)
from juego.rutas_app import (
    get_data_questions_path,
    get_data_root,
    get_resource_audio_dir,
    get_resource_images_dir,
    get_resource_root,
    get_user_images_dir,
)
from juego.servicio_tts import TTSService


class ReviewScreen:
    BASE_DIMENSIONS = GAME_BASE_DIMENSIONS
    SCALE_LIMITS = GAME_SCALE_LIMITS
    RESIZE_DELAY = GAME_RESIZE_DELAY
    COLORS = GAME_COLORS
    ICONS = GAME_ICONS
    BASE_SIZES = GAME_BASE_SIZES

    def __init__(
        self, parent, on_return_callback=None, tts_service=None, sfx_service=None
    ):
        self.parent = parent
        self.on_return_callback = on_return_callback
        self.sfx = sfx_service

        # State
        self.questions = []
        self.current_index = 0
        self.current_question = None
        self.current_image = None
        self.cached_original_image = None
        self.cached_image_path = None
        self.audio_enabled = True
        self.resize_job = None
        self.definition_scroll_update_job = None
        self.definition_scroll_delayed_job = None
        self.ultimo_tam_imagen = 0

        # UI references
        self.main = None
        self.header_frame = None
        self.header_left_container = None
        self.header_center_container = None
        self.header_right_container = None
        self.audio_container = None
        self.audio_toggle_btn = None
        self.audio_icon_on = None
        self.audio_icon_off = None
        self.question_counter_label = None
        self.question_container = None
        self.image_frame = None
        self.image_label = None
        self.definition_frame = None
        self.definition_scroll_wrapper = None
        self.definition_scroll = None
        self.def_inner = None
        self.definition_label = None
        self.definition_scrollbar_visible = None
        self.definition_scrollbar_manager = None
        self.info_icon = None
        self.info_icon_label = None
        self.answer_boxes_frame = None
        self.answer_box_labels = []
        self.nav_buttons_frame = None
        self.prev_button = None
        self.next_button = None
        self.return_button = None

        # Fonts (set by font_registry.attach_attributes)
        self.timer_font = None
        self.score_font = None
        self.definition_font = None
        self.keyboard_font = None
        self.answer_box_font = None
        self.button_font = None
        self.header_button_font = None
        self.header_label_font = None
        self.feedback_font = None
        self.wildcard_font = None
        self.charges_font = None
        self.multiplier_font = None

        # Paths & services
        resource_images_dir = get_resource_images_dir()
        resource_audio_dir = get_resource_audio_dir()
        data_root = get_data_root()
        resource_root = get_resource_root()

        self.images_dir = resource_images_dir
        self.audio_dir = resource_audio_dir
        self.questions_path = get_data_questions_path()

        self.image_handler = ImageHandler(
            self.images_dir,
            user_images_dir=get_user_images_dir(),
            data_root=data_root,
            resource_root=resource_root,
        )

        self.tts = tts_service or TTSService(self.audio_dir)

        if self.sfx and hasattr(self.sfx, "is_muted"):
            self.audio_enabled = not self.sfx.is_muted()

        # Responsive system
        self.scaler = ResponsiveScaler(
            self.BASE_DIMENSIONS,
            self.SCALE_LIMITS,
            global_scale_factor=GAME_GLOBAL_SCALE_FACTOR,
        )
        self.size_calc = GameSizeCalculator(self.scaler, GAME_PROFILES)
        self.font_registry = GameFontRegistry(GAME_FONT_SPECS)
        self.font_registry.attach_attributes(self)
        self.font_base_sizes = self.font_registry.base_sizes
        self.font_min_sizes = self.font_registry.min_sizes

        self.current_scale = 1.0
        self.current_window_width = self.BASE_DIMENSIONS[0]
        self.current_window_height = self.BASE_DIMENSIONS[1]
        self.size_state = {}

        # Load questions and build
        self.load_questions()
        self.build_ui()

        # Bind resize
        self.parent.bind("<Configure>", self.on_resize)

        # Bind keyboard for navigation
        self._keypress_bind_id = self.parent.winfo_toplevel().bind(
            "<KeyPress>", self._on_key_press
        )

        # Initial layout
        self.apply_responsive()

        # Show first question
        if self.questions:
            self.show_question(0)

    def load_questions(self):
        try:
            with open(self.questions_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.questions = data.get("questions", [])
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading questions: {e}")
            self.questions = []

    def build_ui(self):
        for widget in self.parent.winfo_children():
            widget.destroy()

        self.parent.grid_rowconfigure(0, weight=1)
        self.parent.grid_columnconfigure(0, weight=1)

        self.main = ctk.CTkFrame(self.parent, fg_color=self.COLORS["bg_light"])
        self.main.grid(row=0, column=0, sticky="nsew")

        # Layout: header, question container, nav buttons, return button
        self.main.grid_rowconfigure(0, weight=0)  # Header
        self.main.grid_rowconfigure(1, weight=1)  # Question container
        self.main.grid_rowconfigure(2, weight=0)  # Navigation buttons
        self.main.grid_rowconfigure(3, weight=0)  # Return button
        self.main.grid_columnconfigure(0, weight=1)

        self.build_header()
        self.build_question_container()
        self.build_nav_buttons()
        self.build_return_button()

    def build_header(self):
        header_height = self.BASE_SIZES["header_height"]

        self.header_frame = ctk.CTkFrame(
            self.main,
            fg_color=self.COLORS["header_bg"],
            height=header_height,
            corner_radius=0,
        )
        self.header_frame.grid(row=0, column=0, sticky="ew")
        self.header_frame.grid_propagate(False)

        self.header_frame.grid_columnconfigure(0, weight=1, uniform="header_side")
        self.header_frame.grid_columnconfigure(1, weight=0)
        self.header_frame.grid_columnconfigure(2, weight=1, uniform="header_side")
        self.header_frame.grid_rowconfigure(0, weight=1)

        # Left container - empty placeholder for symmetry
        self.header_left_container = ctk.CTkFrame(
            self.header_frame, fg_color="transparent"
        )
        self.header_left_container.grid(
            row=0, column=0, sticky="w", padx=(self.BASE_SIZES["header_pad_x"], 0)
        )

        # Center - question counter
        self.header_center_container = ctk.CTkFrame(
            self.header_frame, fg_color="transparent"
        )
        self.header_center_container.grid(row=0, column=1)

        self.question_counter_label = ctk.CTkLabel(
            self.header_center_container,
            text="0 / 0",
            font=self.score_font,
            text_color="white",
        )
        self.question_counter_label.grid(row=0, column=0)

        # Right container - audio toggle
        self.header_right_container = ctk.CTkFrame(
            self.header_frame, fg_color="transparent"
        )
        self.header_right_container.grid(
            row=0, column=2, sticky="e", padx=(0, self.BASE_SIZES["header_pad_x"])
        )

        self.build_audio_section()

    def build_audio_section(self):
        self.audio_container = ctk.CTkFrame(
            self.header_right_container, fg_color="transparent"
        )
        self.audio_container.grid(row=0, column=0)

        self.load_audio_icons()

        self.audio_toggle_btn = ctk.CTkButton(
            self.audio_container,
            text="",
            image=self.audio_icon_on,
            font=self.timer_font,
            width=self.BASE_SIZES["audio_button_width"],
            height=self.BASE_SIZES["audio_button_height"],
            fg_color="transparent",
            hover_color=self.COLORS["header_hover"],
            text_color="white",
            corner_radius=8,
            command=self.toggle_audio,
        )
        self.audio_toggle_btn.grid(row=0, column=0)
        self.update_audio_button_icon()

    def build_question_container(self):
        self.question_container = ctk.CTkFrame(
            self.main,
            fg_color=self.COLORS["bg_card"],
            corner_radius=self.BASE_SIZES["container_corner_radius"],
            border_width=2,
            border_color=self.COLORS["border_light"],
        )
        self.question_container.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=self.BASE_SIZES["container_pad_x"],
            pady=(self.BASE_SIZES["container_pad_y"], 0),
        )

        self.question_container.grid_columnconfigure(0, weight=1)
        for r in range(3):
            self.question_container.grid_rowconfigure(r, weight=0)

        self.build_image_section()
        self.build_definition_section()
        self.build_answer_boxes_section()

    def build_image_section(self):
        img_sz = self.get_scaled_image_size()

        self.image_frame = ctk.CTkFrame(
            self.question_container, fg_color="transparent", height=img_sz
        )
        self.image_frame.grid(row=0, column=0, pady=(12, 6))
        self.image_frame.grid_rowconfigure(0, weight=1)
        self.image_frame.grid_columnconfigure(0, weight=1)

        self.image_label = ctk.CTkLabel(
            self.image_frame,
            text="",
            fg_color=self.COLORS["bg_light"],
            corner_radius=16,
            width=img_sz,
            height=img_sz,
        )
        self.image_label.grid(row=0, column=0)

    def build_definition_section(self):
        self.definition_frame = ctk.CTkFrame(
            self.question_container, fg_color="transparent"
        )
        self.definition_frame.grid(row=1, column=0, sticky="ew", padx=24, pady=2)
        self.definition_frame.grid_columnconfigure(0, weight=1)

        self.load_info_icon()

        self.definition_scroll_wrapper = ctk.CTkFrame(
            self.definition_frame,
            fg_color="transparent",
            height=45,
        )
        self.definition_scroll_wrapper.grid(row=0, column=0, sticky="ew")
        self.definition_scroll_wrapper.grid_propagate(False)
        self.definition_scroll_wrapper.grid_rowconfigure(0, weight=1)
        self.definition_scroll_wrapper.grid_columnconfigure(0, weight=1)

        self.definition_scroll = ctk.CTkScrollableFrame(
            self.definition_scroll_wrapper,
            fg_color="transparent",
            scrollbar_button_color="#9B9B9B",
            scrollbar_button_hover_color="#666666",
        )
        self.definition_scroll.grid(row=0, column=0, sticky="nsew")
        self.definition_scroll.grid_columnconfigure(0, weight=1)

        self.def_inner = ctk.CTkFrame(self.definition_scroll, fg_color="transparent")
        self.def_inner.master.grid_columnconfigure(0, weight=1)
        self.def_inner.grid(row=0, column=0, sticky="")
        self.def_inner.grid_columnconfigure(1, weight=1)

        self.info_icon_label = ctk.CTkLabel(
            self.def_inner, text="", image=self.info_icon
        )
        self.info_icon_label.grid(row=0, column=0, sticky="n", padx=(0, 8), pady=(2, 0))

        self.definition_label = ctk.CTkLabel(
            self.def_inner,
            text="Loading questions...",
            font=self.definition_font,
            text_color=self.COLORS["text_medium"],
            wraplength=self.BASE_SIZES["definition_wrap_base"],
            justify="left",
            anchor="w",
        )
        self.definition_label.grid(row=0, column=1, sticky="nw")

    def build_answer_boxes_section(self):
        box_sz = self.get_scaled_box_size()

        self.answer_boxes_frame = ctk.CTkFrame(
            self.question_container,
            fg_color="transparent",
            width=10 * (box_sz + 8),
            height=box_sz + 16,
        )
        self.answer_boxes_frame.grid(row=2, column=0, pady=(6, 12), padx=20)
        self.answer_boxes_frame.grid_rowconfigure(0, weight=1)
        self.answer_boxes_frame.grid_anchor("center")

    def build_nav_buttons(self):
        self.nav_buttons_frame = ctk.CTkFrame(self.main, fg_color="transparent")
        self.nav_buttons_frame.grid(row=2, column=0, pady=(16, 8))

        btn_width = self.BASE_SIZES["action_button_width"]
        btn_height = self.BASE_SIZES["action_button_height"]
        btn_gap = self.BASE_SIZES["action_button_gap"] * 2  # More gap between buttons
        corner_r = self.BASE_SIZES["action_corner_radius"]

        self.prev_button = ctk.CTkButton(
            self.nav_buttons_frame,
            text="← Previous",
            font=self.button_font,
            width=btn_width,
            height=btn_height,
            fg_color=self.COLORS["bg_light"],
            hover_color=self.COLORS["border_medium"],
            text_color="black",
            border_width=2,
            border_color="black",
            corner_radius=corner_r,
            command=self.prev_question,
        )
        self.prev_button.grid(row=0, column=0, padx=btn_gap // 2)

        self.next_button = ctk.CTkButton(
            self.nav_buttons_frame,
            text="Next →",
            font=self.button_font,
            width=btn_width,
            height=btn_height,
            fg_color=self.COLORS["primary_blue"],
            hover_color=self.COLORS["primary_hover"],
            text_color="white",
            corner_radius=corner_r,
            command=self.next_question,
        )
        self.next_button.grid(row=0, column=1, padx=btn_gap // 2)

    def build_return_button(self):
        self.return_button = ctk.CTkButton(
            self.main,
            text="Return to Menu",
            font=self.button_font,
            width=self.BASE_SIZES["action_button_width"] + 40,
            height=self.BASE_SIZES["action_button_height"],
            fg_color=self.COLORS["danger_red"],
            hover_color=self.COLORS["danger_hover"],
            text_color="white",
            corner_radius=self.BASE_SIZES["action_corner_radius"],
            command=self.return_to_menu,
        )
        self.return_button.grid(row=3, column=0, pady=(8, 24))

    def load_icon(self, icon_key, size):
        return self.image_handler.create_ctk_icon(self.ICONS[icon_key], (size, size))

    def load_audio_icons(self):
        sz = self.BASE_SIZES["audio_icon_base"]
        self.audio_icon_on = self.load_icon("volume_on", sz)
        self.audio_icon_off = self.load_icon("volume_off", sz)

    def load_info_icon(self):
        self.info_icon = self.load_icon("info", 24)

    def update_audio_button_icon(self):
        if not self.audio_toggle_btn:
            return
        icon = self.audio_icon_on if self.audio_enabled else self.audio_icon_off
        if icon:
            self.audio_toggle_btn.configure(image=icon, text="")
        else:
            self.audio_toggle_btn.configure(
                image=None, text="On" if self.audio_enabled else "Off"
            )

    def show_question(self, index):
        if not self.questions:
            self.set_definition_text("No questions available!")
            return

        self.current_index = max(0, min(index, len(self.questions) - 1))
        self.current_question = self.questions[self.current_index]

        # Update counter
        self.question_counter_label.configure(
            text=f"{self.current_index + 1} / {len(self.questions)}"
        )

        # Update definition
        definition = self.current_question.get("definition", "No definition")
        self.set_definition_text(definition)

        # Create answer boxes filled with correct answer
        title = self.current_question.get("title", "")
        title_no_spaces = title.replace(" ", "")
        self.create_answer_boxes_filled(title_no_spaces)

        # Load image
        self.cached_original_image = None
        self.cached_image_path = None
        self.load_question_image()

        # Speak definition if audio enabled
        self.tts.stop()
        if self.audio_enabled and definition and definition != "No definition":
            self.tts.speak(definition)

        # Update nav button states
        self.update_nav_buttons_state()

    def create_answer_boxes_filled(self, answer_text):
        box_sz = self.get_scaled_box_size()
        gap = self.size_state.get("answer_box_gap", 3) if self.size_state else 3
        scale = self.size_state.get("scale", 1.0) if self.size_state else 1.0
        is_compact = (
            self.size_state.get("is_height_constrained", False)
            if self.size_state
            else False
        )
        extra_pad = self.scale_value(16, scale, 8, 20)

        word_length = len(answer_text)

        # Create new boxes if needed
        for i in range(len(self.answer_box_labels), word_length):
            box = ctk.CTkLabel(
                self.answer_boxes_frame,
                text="",
                font=self.answer_box_font,
                width=box_sz,
                height=box_sz,
                fg_color=self.COLORS["answer_box_empty"],
                corner_radius=8,
                text_color=self.COLORS["text_dark"],
            )
            self.answer_box_labels.append(box)

        # Fill boxes with correct answer
        for i in range(word_length):
            box = self.answer_box_labels[i]
            letter = answer_text[i].upper()
            box.configure(
                text=letter,
                fg_color=self.COLORS["success_green"],
                width=box_sz,
                height=box_sz,
            )
            box.grid(row=0, column=i, padx=gap, pady=4)

        # Hide excess boxes
        excess_count = len(self.answer_box_labels) - word_length
        if excess_count > 10:
            for i in range(word_length + 10, len(self.answer_box_labels)):
                try:
                    self.answer_box_labels[i].destroy()
                except tk.TclError:
                    pass
            del self.answer_box_labels[word_length + 10 :]

        for i in range(word_length, len(self.answer_box_labels)):
            self.answer_box_labels[i].grid_remove()

        # Update frame size
        self.answer_boxes_frame.configure(
            width=max(box_sz, word_length * (box_sz + gap * 2)),
            height=box_sz + extra_pad,
        )
        if self.answer_boxes_frame and self.answer_boxes_frame.winfo_exists():
            if is_compact:
                pad_y = self.scale_value(8, scale, 6, 12)
            else:
                pad_y = self.scale_value(14, scale, 8, 28)
            self.answer_boxes_frame.grid_configure(pady=(pad_y, pad_y // 2))

    def load_question_image(self):
        if not self.current_question:
            return

        image_path = self.current_question.get("image", "")
        if not image_path:
            self.image_label.configure(image=None, text="No Image")
            self.current_image = None
            self.cached_original_image = None
            self.cached_image_path = None
            return

        try:
            if (
                self.cached_original_image is None
                or self.cached_image_path != image_path
            ):
                resolved_path = None
                if self.image_handler:
                    resolved_path = self.image_handler.resolve_image_path(image_path)

                if resolved_path and resolved_path.exists():
                    with Image.open(resolved_path) as img:
                        self.cached_original_image = img.convert("RGBA").copy()
                        self.cached_image_path = image_path
                else:
                    self.image_label.configure(image=None, text="Image not found")
                    self.current_image = None
                    self.cached_original_image = None
                    self.cached_image_path = None
                    return

            if self.cached_original_image:
                max_sz = self.get_scaled_image_size()
                w, h = self.cached_original_image.size
                if w > 0 and h > 0:
                    sc = min(max_sz / w, max_sz / h)
                    self.current_image = ctk.CTkImage(
                        light_image=self.cached_original_image,
                        dark_image=self.cached_original_image,
                        size=(int(w * sc), int(h * sc)),
                    )
                    self.image_label.configure(image=self.current_image, text="")
            else:
                self.image_label.configure(image=None, text="Image Error")
                self.current_image = None

        except (FileNotFoundError, OSError, ValueError) as e:
            print(f"Error loading image: {e}")
            self.image_label.configure(image=None, text="Error loading image")
            self.current_image = None

    def next_question(self):
        if self.questions and self.current_index < len(self.questions) - 1:
            self.show_question(self.current_index + 1)

    def prev_question(self):
        if self.questions and self.current_index > 0:
            self.show_question(self.current_index - 1)

    def update_nav_buttons_state(self):
        if not self.questions:
            self.prev_button.configure(state="disabled")
            self.next_button.configure(state="disabled")
            return

        if self.current_index <= 0:
            self.prev_button.configure(
                state="disabled",
                fg_color=self.COLORS["border_medium"],
                border_color=self.COLORS["border_medium"],
                text_color=self.COLORS["text_light"],
            )
        else:
            self.prev_button.configure(
                state="normal",
                fg_color=self.COLORS["bg_light"],
                border_color="black",
                text_color="black",
            )

        if self.current_index >= len(self.questions) - 1:
            self.next_button.configure(
                state="disabled",
                fg_color=self.COLORS["border_medium"],
                hover_color=self.COLORS["border_medium"],
            )
        else:
            self.next_button.configure(
                state="normal",
                fg_color=self.COLORS["primary_blue"],
                hover_color=self.COLORS["primary_hover"],
            )

    def toggle_audio(self):
        self.audio_enabled = not self.audio_enabled
        self.update_audio_button_icon()
        if self.sfx:
            self.sfx.set_muted(not self.audio_enabled)
        if self.audio_enabled and self.current_question:
            defn = self.current_question.get("definition", "").strip()
            if defn:
                self.tts.speak(defn)
        else:
            self.tts.stop()

    def return_to_menu(self):
        self.cleanup()
        if self.on_return_callback:
            self.on_return_callback()

    def _on_key_press(self, event):
        key_sym = event.keysym
        if key_sym in ("Right", "Next"):
            self.next_question()
        elif key_sym in ("Left", "Prior"):
            self.prev_question()
        elif key_sym == "Escape":
            self.return_to_menu()

    def get_logical_dimensions(self):
        return get_logical_dimensions(self.parent, self.BASE_DIMENSIONS)

    def scale_value(self, base, scale, min_value=None, max_value=None):
        return self.scaler.scale_value(base, scale, min_value, max_value)

    def get_scaled_image_size(self, scale=None):
        if self.size_state and "image_size" in self.size_state:
            return self.size_state["image_size"]
        s = scale or self._get_current_scale()
        return self.scale_value(
            self.BASE_SIZES["image_base"],
            s,
            self.BASE_SIZES["image_min"],
            self.BASE_SIZES["image_max"],
        )

    def get_scaled_box_size(self, scale=None):
        if self.size_state and "answer_box" in self.size_state:
            return self.size_state["answer_box"]
        s = scale or self._get_current_scale()
        return self.scale_value(
            self.BASE_SIZES["answer_box_base"],
            s,
            self.BASE_SIZES["answer_box_min"],
            self.BASE_SIZES["answer_box_max"],
        )

    def _get_current_scale(self):
        w, h = self.get_logical_dimensions()
        low_res_profile = GAME_PROFILES.get("low_res")
        return self.scaler.calculate_scale(w, h, low_res_profile)

    def on_resize(self, event):
        if event.widget is not self.parent:
            return
        if self.resize_job:
            self.parent.after_cancel(self.resize_job)
        self.resize_job = self.parent.after(self.RESIZE_DELAY, self.apply_responsive)

    def apply_responsive(self):
        if not self.parent or not self.parent.winfo_exists():
            return

        width, height = self.get_logical_dimensions()

        low_res_profile = GAME_PROFILES.get("low_res")
        scale = self.scaler.calculate_scale(width, height, low_res_profile)

        self.size_state = self.size_calc.calculate_sizes(scale, width, height)
        self.current_scale = scale
        self.current_window_width = width
        self.current_window_height = height

        # Update fonts
        self.font_registry.update_scale(scale, self.scaler)

        # Update header
        self.update_header(scale)

        # Update question container
        self.update_question_container()

        # Update nav buttons
        self.update_nav_buttons(scale)

        # Update return button
        self.update_return_button(scale)

        self.resize_job = None

    def update_header(self, scale):
        sizes = self.size_state

        if self.header_frame and self.header_frame.winfo_exists():
            self.header_frame.configure(height=sizes["header_height"])

        pad_x = sizes["header_pad_x"]
        pad_y = sizes["header_pad_y"]

        if self.header_left_container and self.header_left_container.winfo_exists():
            self.header_left_container.grid_configure(padx=(pad_x, 0), pady=pad_y)

        if self.header_right_container and self.header_right_container.winfo_exists():
            self.header_right_container.grid_configure(padx=(0, pad_x), pady=pad_y)

        if self.header_center_container and self.header_center_container.winfo_exists():
            self.header_center_container.grid_configure(pady=pad_y)

        # Audio button
        icon_sz = sizes["audio_icon"]
        btn_width = sizes["audio_button_width"]
        btn_height = sizes["audio_button_height"]
        corner_r = self.scale_value(8, scale, 6, 16)

        for icon in (self.audio_icon_on, self.audio_icon_off):
            if icon:
                icon.configure(size=(icon_sz, icon_sz))

        if self.audio_toggle_btn and self.audio_toggle_btn.winfo_exists():
            self.audio_toggle_btn.configure(
                width=btn_width, height=btn_height, corner_radius=corner_r
            )

    def update_question_container(self):
        sizes = self.size_state

        if not self.question_container or not self.question_container.winfo_exists():
            return

        pad_x = sizes["container_pad_x"]
        pad_y = sizes["container_pad_y"]
        corner_r = sizes["container_corner_radius"]

        self.question_container.grid_configure(padx=pad_x, pady=(pad_y, 0))
        self.question_container.configure(corner_radius=corner_r)

        self.update_image()
        self.update_definition()
        self.update_answer_boxes()

    def update_image(self):
        sizes = self.size_state
        scale = sizes.get("scale", 1.0)
        is_compact = sizes.get("is_height_constrained", False)
        img_sz = sizes["image_size"]

        if self.image_frame and self.image_frame.winfo_exists():
            self.image_frame.configure(height=img_sz)
            if is_compact:
                pad_top = self.scale_value(12, scale, 6, 20)
                pad_bottom = self.scale_value(6, scale, 3, 10)
            else:
                pad_top = self.scale_value(24, scale, 12, 60)
                pad_bottom = self.scale_value(12, scale, 6, 30)
            self.image_frame.grid_configure(pady=(pad_top, pad_bottom))

        if self.image_label and self.image_label.winfo_exists():
            self.image_label.configure(width=img_sz, height=img_sz)

        # Reload image if size changed significantly
        if self.current_image and self.current_question:
            nuevo_tam = self.size_state.get("image_size", img_sz)
            tam_actual = getattr(self, "ultimo_tam_imagen", 0)
            if abs(nuevo_tam - tam_actual) > 2:
                self.ultimo_tam_imagen = nuevo_tam
                self.load_question_image()

    def update_definition(self):
        sizes = self.size_state
        scale = sizes.get("scale", 1.0)

        if self.definition_frame and self.definition_frame.winfo_exists():
            pad_x = sizes.get("definition_pad_x")
            pad_y = sizes.get("definition_pad_y")
            if pad_x is None:
                pad_x = self.scale_value(36, scale, 20, 80)
            if pad_y is None:
                pad_y = self.scale_value(14, scale, 8, 36)
            self.definition_frame.grid_configure(padx=pad_x, pady=pad_y)

        if (
            self.definition_scroll_wrapper
            and self.definition_scroll_wrapper.winfo_exists()
        ):
            max_height = sizes.get("definition_height")
            if max_height is None:
                if sizes.get("is_height_constrained", False):
                    max_height = self.scale_value(42, scale, 38, 50)
                else:
                    if sizes.get("window_height", 0) >= 1080:
                        max_height = self.scale_value(70, scale, 50, 110)
                    else:
                        max_height = self.scale_value(50, scale, 42, 65)
            self.definition_scroll_wrapper.configure(height=max_height)

        if self.definition_label and self.definition_label.winfo_exists():
            wrap = sizes["definition_wrap"]
            self.definition_label.configure(wraplength=wrap)

        if self.info_icon:
            sz = sizes["info_icon"]
            self.info_icon.configure(size=(sz, sz))

        self.queue_definition_scroll_update()

    def update_answer_boxes(self):
        sizes = self.size_state
        scale = sizes.get("scale", 1.0)
        is_compact = sizes.get("is_height_constrained", False)
        box_sz = sizes["answer_box"]
        gap = sizes["answer_box_gap"]
        extra_pad = self.scale_value(16, scale, 8, 20)

        visible_boxes = [b for b in self.answer_box_labels if b.winfo_manager()]
        for box in visible_boxes:
            if box and box.winfo_exists():
                box.configure(width=box_sz, height=box_sz)
                box.grid_configure(padx=gap, pady=4)

        if (
            visible_boxes
            and self.answer_boxes_frame
            and self.answer_boxes_frame.winfo_exists()
        ):
            frame_width = len(visible_boxes) * (box_sz + gap * 2)
            frame_height = box_sz + extra_pad
            self.answer_boxes_frame.configure(width=frame_width, height=frame_height)
            if is_compact:
                pad_y = self.scale_value(8, scale, 6, 12)
            else:
                pad_y = self.scale_value(14, scale, 8, 28)
            self.answer_boxes_frame.grid_configure(pady=(pad_y, pad_y // 2))

    def update_nav_buttons(self, scale):
        sizes = self.size_state
        btn_width = sizes["action_button_width"]
        btn_height = sizes["action_button_height"]
        btn_gap = sizes["action_button_gap"] * 2
        corner_r = sizes["action_corner_radius"]

        for btn in [self.prev_button, self.next_button]:
            if btn and btn.winfo_exists():
                btn.configure(
                    width=btn_width,
                    height=btn_height,
                    corner_radius=corner_r,
                )
                btn.grid_configure(padx=btn_gap // 2)

        if self.nav_buttons_frame and self.nav_buttons_frame.winfo_exists():
            pad_top = self.scale_value(16, scale, 8, 32)
            pad_bottom = self.scale_value(8, scale, 4, 16)
            self.nav_buttons_frame.grid_configure(pady=(pad_top, pad_bottom))

    def update_return_button(self, scale):
        sizes = self.size_state
        btn_width = sizes["action_button_width"] + 40
        btn_height = sizes["action_button_height"]
        corner_r = sizes["action_corner_radius"]

        if self.return_button and self.return_button.winfo_exists():
            self.return_button.configure(
                width=btn_width,
                height=btn_height,
                corner_radius=corner_r,
            )
            pad_top = self.scale_value(8, scale, 4, 16)
            pad_bottom = self.scale_value(24, scale, 12, 48)
            self.return_button.grid_configure(pady=(pad_top, pad_bottom))

    def set_definition_text(self, text):
        if self.definition_label and self.definition_label.winfo_exists():
            self.definition_label.configure(text=text)
        self.queue_definition_scroll_update()

    def queue_definition_scroll_update(self):
        if not self.parent or not self.parent.winfo_exists():
            return
        if self.definition_scroll_update_job:
            try:
                self.parent.after_cancel(self.definition_scroll_update_job)
            except tk.TclError:
                pass
            self.definition_scroll_update_job = None
        if self.definition_scroll_delayed_job:
            try:
                self.parent.after_cancel(self.definition_scroll_delayed_job)
            except tk.TclError:
                pass
            self.definition_scroll_delayed_job = None
        try:
            self.definition_scroll_update_job = self.parent.after_idle(
                self._on_scroll_idle_check
            )
        except tk.TclError:
            self.definition_scroll_update_job = None
            self.update_definition_scrollbar_visibility()

    def _on_scroll_idle_check(self):
        self.definition_scroll_update_job = None
        self.update_definition_scrollbar_visibility()
        if self.parent and self.parent.winfo_exists():
            try:
                self.definition_scroll_delayed_job = self.parent.after(
                    150, self._on_scroll_delayed_check
                )
            except tk.TclError:
                pass

    def _on_scroll_delayed_check(self):
        self.definition_scroll_delayed_job = None
        self.update_definition_scrollbar_visibility()

    def update_definition_scrollbar_visibility(self):
        self.definition_scroll_update_job = None
        if not self.definition_scroll or not self.definition_scroll.winfo_exists():
            return
        if (
            not self.definition_scroll_wrapper
            or not self.definition_scroll_wrapper.winfo_exists()
        ):
            return

        content = None
        if self.def_inner and self.def_inner.winfo_exists():
            content = self.def_inner
        elif self.definition_label and self.definition_label.winfo_exists():
            content = self.definition_label
        if not content:
            return

        try:
            content.update_idletasks()
            self.definition_scroll_wrapper.update_idletasks()
        except tk.TclError:
            return

        wrapper_height = self.definition_scroll_wrapper.winfo_height()
        if wrapper_height <= 1:
            wrapper_height = self.definition_scroll_wrapper.winfo_reqheight()
        content_height = content.winfo_reqheight()

        needs_scroll = content_height > wrapper_height
        self.set_definition_scrollbar_visible(needs_scroll)

    def set_definition_scrollbar_visible(self, visible):
        if self.definition_scrollbar_visible is visible:
            return

        scrollbar = self._get_scrollbar_widget(self.definition_scroll)
        if not scrollbar or not scrollbar.winfo_exists():
            return

        manager = self.definition_scrollbar_manager or scrollbar.winfo_manager()
        if not manager:
            manager = "grid"
        self.definition_scrollbar_manager = manager

        if visible:
            if manager == "grid":
                scrollbar.grid()
            elif manager == "pack":
                scrollbar.pack()
            elif manager == "place":
                scrollbar.place()
        else:
            if manager == "grid":
                scrollbar.grid_remove()
            elif manager == "pack":
                scrollbar.pack_forget()
            elif manager == "place":
                scrollbar.place_forget()

        self.definition_scrollbar_visible = visible

    def _get_scrollbar_widget(self, scrollable):
        if not scrollable:
            return None
        for attr in (
            "_scrollbar",
            "_scrollbar_vertical",
            "_y_scrollbar",
            "_scrollbar_y",
        ):
            scrollbar = getattr(scrollable, attr, None)
            if scrollbar:
                return scrollbar
        return None

    def cleanup(self):
        self.tts.stop()

        if self.resize_job:
            try:
                self.parent.after_cancel(self.resize_job)
            except (tk.TclError, ValueError):
                pass
            self.resize_job = None

        if self.definition_scroll_update_job:
            try:
                self.parent.after_cancel(self.definition_scroll_update_job)
            except (tk.TclError, ValueError):
                pass
            self.definition_scroll_update_job = None

        if self.definition_scroll_delayed_job:
            try:
                self.parent.after_cancel(self.definition_scroll_delayed_job)
            except (tk.TclError, ValueError):
                pass
            self.definition_scroll_delayed_job = None

        try:
            self.parent.unbind("<Configure>")
        except tk.TclError:
            pass

        try:
            root = self.parent.winfo_toplevel()
            if hasattr(self, "_keypress_bind_id") and self._keypress_bind_id:
                root.unbind("<KeyPress>", self._keypress_bind_id)
                self._keypress_bind_id = None
        except tk.TclError:
            pass

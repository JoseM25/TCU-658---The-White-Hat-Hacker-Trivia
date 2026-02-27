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

        # Estado
        self.questions, self.answer_box_labels = [], []
        self.current_index, self.ultimo_tam_imagen = 0, 0
        self.current_question = self.current_image = self.cached_original_image = (
            self.cached_image_path
        ) = None
        self.resize_job = self.definition_scroll_update_job = (
            self.definition_scroll_delayed_job
        ) = None
        self.audio_enabled = True

        # Referencias de interfaz
        self.main = self.header_frame = self.header_left_container = (
            self.header_center_container
        ) = self.header_right_container = None
        self.audio_container = self.audio_toggle_btn = self.audio_icon_on = (
            self.audio_icon_off
        ) = None
        self.menu_icon = None
        self.question_counter_label = self.question_container = self.image_frame = (
            self.image_label
        ) = None
        self.definition_frame = self.definition_scroll_wrapper = (
            self.definition_scroll
        ) = self.def_inner = None
        self.definition_label = self.definition_scrollbar_visible = (
            self.definition_scrollbar_manager
        ) = None
        self.info_icon = self.info_icon_label = self.answer_boxes_frame = (
            self.bottom_container
        ) = None
        self.nav_buttons_frame = self.prev_button = self.next_button = None
        self.menu_button = None

        # Fuentes (se asignan con font_registry.attach_attributes)
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

        # Rutas y servicios
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

        # Sistema responsivo
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

        # Cargar preguntas y construir interfaz
        self.load_questions()
        self.build_ui()

        # Vincular redimensionamiento
        self.parent.bind("<Configure>", self.on_resize)

        # Vincular teclado para navegación
        self._keypress_bind_id = self.parent.winfo_toplevel().bind(
            "<KeyPress>", self._on_key_press
        )

        # Diseño inicial
        self.apply_responsive()

        # Mostrar primera pregunta
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

        for i, w in enumerate([0, 1, 0, 0]):
            self.main.grid_rowconfigure(i, weight=w)
        self.main.grid_columnconfigure(0, weight=1)

        self.build_header()
        self.build_question_container()

        self.bottom_container = ctk.CTkFrame(self.main, fg_color="transparent")
        self.bottom_container.grid(row=2, column=0, rowspan=2, sticky="nsew")
        self.bottom_container.grid_columnconfigure(0, weight=1)
        for i in (0, 1):
            self.bottom_container.grid_rowconfigure(i, weight=1)

        self.build_nav_buttons()

    def build_header(self):
        hf = ctk.CTkFrame(
            self.main,
            fg_color=self.COLORS["header_bg"],
            height=self.BASE_SIZES["header_height"],
            corner_radius=0,
        )
        hf.grid(row=0, column=0, sticky="ew")
        hf.grid_propagate(False)
        hf.grid_columnconfigure((0, 2), weight=1, uniform="header_side")
        hf.grid_columnconfigure(1, weight=0)
        hf.grid_rowconfigure(0, weight=1)
        self.header_frame = hf

        pad_x = self.BASE_SIZES["header_pad_x"]
        conts = [ctk.CTkFrame(hf, fg_color="transparent") for _ in range(3)]
        (
            self.header_left_container,
            self.header_center_container,
            self.header_right_container,
        ) = conts

        conts[0].grid(row=0, column=0, sticky="w", padx=(pad_x, 0))
        conts[1].grid(row=0, column=1)
        conts[2].grid(row=0, column=2, sticky="e", padx=(0, pad_x))

        self.menu_icon = self.load_icon("arrow", self.BASE_SIZES["audio_icon_base"])
        self.menu_button = ctk.CTkButton(
            conts[0],
            text="Menu",
            font=self.header_button_font or self.button_font,
            text_color="white",
            image=self.menu_icon,
            compound="left",
            fg_color="transparent",
            hover_color=self.COLORS["header_hover"],
            corner_radius=8,
            width=110,
            height=44,
            anchor="w",
            command=self.return_to_menu,
        )
        self.menu_button.grid(row=0, column=0, sticky="w")

        self.question_counter_label = ctk.CTkLabel(
            conts[1], text="0 / 0", font=self.score_font, text_color="white"
        )
        self.question_counter_label.grid(row=0, column=0)

        self.load_audio_icons()
        self.audio_toggle_btn = ctk.CTkButton(
            conts[2],
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
        df = ctk.CTkFrame(self.question_container, fg_color="transparent")
        df.grid(row=1, column=0, sticky="ew", padx=24, pady=2)
        df.grid_columnconfigure(0, weight=1)
        self.definition_frame = df

        self.load_info_icon()

        dsw = ctk.CTkFrame(df, fg_color="transparent", height=45)
        dsw.grid(row=0, column=0, sticky="ew")
        dsw.grid_propagate(False)
        dsw.grid_rowconfigure(0, weight=1)
        dsw.grid_columnconfigure(0, weight=1)
        self.definition_scroll_wrapper = dsw

        ds = ctk.CTkScrollableFrame(
            dsw,
            fg_color="transparent",
            scrollbar_button_color="#9B9B9B",
            scrollbar_button_hover_color="#666666",
        )
        ds.grid(row=0, column=0, sticky="nsew")
        ds.grid_columnconfigure(0, weight=1)
        self.definition_scroll = ds

        di = ctk.CTkFrame(ds, fg_color="transparent")
        di.master.grid_columnconfigure(0, weight=1)
        di.grid(row=0, column=0, sticky="")
        di.grid_columnconfigure(1, weight=1)
        self.def_inner = di

        self.info_icon_label = ctk.CTkLabel(di, text="", image=self.info_icon)
        self.info_icon_label.grid(row=0, column=0, sticky="n", padx=(0, 8), pady=(2, 0))

        self.definition_label = ctk.CTkLabel(
            di,
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

    def _create_btn(
        self, parent, text, fg, hover, txt_col, cmd, border=0, border_col=""
    ):
        return ctk.CTkButton(
            parent,
            text=text,
            font=self.button_font,
            width=self.BASE_SIZES["action_button_width"],
            height=self.BASE_SIZES["action_button_height"],
            fg_color=fg,
            hover_color=hover,
            text_color=txt_col,
            border_width=border,
            border_color=border_col,
            corner_radius=self.BASE_SIZES["action_corner_radius"],
            command=cmd,
        )

    def build_nav_buttons(self):
        nf = ctk.CTkFrame(self.bottom_container, fg_color="transparent")
        nf.grid(row=0, column=0, pady=(16, 8), sticky="s")
        self.nav_buttons_frame = nf

        self.prev_button = self._create_btn(
            nf,
            "← Previous",
            self.COLORS["bg_light"],
            self.COLORS["border_medium"],
            "black",
            self.prev_question,
            2,
            "black",
        )
        self.next_button = self._create_btn(
            nf,
            "Next →",
            self.COLORS["primary_blue"],
            self.COLORS["primary_hover"],
            "white",
            self.next_question,
        )

        bgap = self.BASE_SIZES["action_button_gap"]
        self.prev_button.grid(row=0, column=0, padx=bgap)
        self.next_button.grid(row=0, column=1, padx=bgap)

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

        self.question_counter_label.configure(
            text=f"{self.current_index + 1} / {len(self.questions)}"
        )

        definition = self.current_question.get("definition", "No definition")
        self.set_definition_text(definition)

        title = self.current_question.get("title", "")
        title_no_spaces = title.replace(" ", "")
        self.create_answer_boxes_filled(title_no_spaces)

        self.cached_original_image = None
        self.cached_image_path = None
        self.load_question_image()

        self.tts.stop()
        if self.audio_enabled and definition and definition != "No definition":
            self.tts.speak(definition)

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

        for i in range(word_length):
            box = self.answer_box_labels[i]
            box.configure(
                text=answer_text[i].upper(),
                fg_color=self.COLORS["success_green"],
                width=box_sz,
                height=box_sz,
            )
            box.grid(row=0, column=i, padx=gap, pady=4)

        if len(self.answer_box_labels) - word_length > 10:
            for box in self.answer_box_labels[word_length + 10 :]:
                try:
                    box.destroy()
                except tk.TclError:
                    pass
            del self.answer_box_labels[word_length + 10 :]

        for i in range(word_length, len(self.answer_box_labels)):
            self.answer_box_labels[i].grid_remove()

        self._safe_config(
            self.answer_boxes_frame,
            width=max(box_sz, word_length * (box_sz + gap * 2)),
            height=box_sz + extra_pad,
        )
        pad_y = self.scale_value(
            8 if is_compact else 14,
            scale,
            6 if is_compact else 8,
            12 if is_compact else 28,
        )
        self._safe_grid(self.answer_boxes_frame, pady=(pad_y, pad_y // 2))

    def load_question_image(self):
        if not self.current_question:
            return
        image_path = self.current_question.get("image", "")
        if not image_path:
            self._clear_image("No Image")
            return

        try:
            if (
                self.cached_original_image is None
                or self.cached_image_path != image_path
            ):
                resolved_path = (
                    self.image_handler.resolve_image_path(image_path)
                    if self.image_handler
                    else None
                )
                if resolved_path and resolved_path.exists():
                    with Image.open(resolved_path) as img:
                        self.cached_original_image = img.convert("RGBA").copy()
                        self.cached_image_path = image_path
                else:
                    self._clear_image("Image not found")
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
                self._clear_image("Image Error")
        except (IOError, OSError, ValueError) as e:
            print(f"Error loading image: {e}")
            self._clear_image("Error loading image")

    def _clear_image(self, text):
        self.image_label.configure(image=None, text=text)
        self.current_image = self.cached_original_image = self.cached_image_path = None

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

        is_first = self.current_index <= 0
        p_cfg = (
            {
                "state": "disabled",
                "fg_color": self.COLORS["border_medium"],
                "border_color": self.COLORS["border_medium"],
                "text_color": self.COLORS["text_light"],
            }
            if is_first
            else {
                "state": "normal",
                "fg_color": self.COLORS["bg_light"],
                "border_color": "black",
                "text_color": "black",
            }
        )
        self.prev_button.configure(**p_cfg)

        is_last = self.current_index >= len(self.questions) - 1
        n_cfg = (
            {
                "state": "disabled",
                "fg_color": self.COLORS["border_medium"],
                "hover_color": self.COLORS["border_medium"],
            }
            if is_last
            else {
                "state": "normal",
                "fg_color": self.COLORS["primary_blue"],
                "hover_color": self.COLORS["primary_hover"],
            }
        )
        self.next_button.configure(**n_cfg)

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

    def _safe_config(self, widget, **kwargs):
        if widget and widget.winfo_exists():
            widget.configure(**kwargs)

    def _safe_grid(self, widget, **kwargs):
        if widget and widget.winfo_exists():
            widget.grid_configure(**kwargs)

    def _cancel_job(self, job_attr):
        job = getattr(self, job_attr, None)
        if job:
            try:
                self.parent.after_cancel(job)
            except (tk.TclError, ValueError):
                pass
            setattr(self, job_attr, None)

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
        return self.scaler.calculate_scale(w, h, GAME_PROFILES.get("low_res"))

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
        scale = self.scaler.calculate_scale(width, height, GAME_PROFILES.get("low_res"))

        self.size_state = self.size_calc.calculate_sizes(scale, width, height)
        self.current_scale = scale
        self.current_window_width = width
        self.current_window_height = height

        self.font_registry.update_scale(scale, self.scaler)
        self.update_header(scale)
        self.update_question_container()
        self.update_nav_buttons(scale)

        self.resize_job = None

    def update_header(self, scale):
        sz = self.size_state
        self._safe_config(self.header_frame, height=sz["header_height"])
        px, py = sz["header_pad_x"], sz["header_pad_y"]
        self._safe_grid(self.header_left_container, padx=(px, 0), pady=py)
        self._safe_grid(self.header_right_container, padx=(0, px), pady=py)
        self._safe_grid(self.header_center_container, pady=py)
        self._safe_config(
            self.menu_button,
            width=self.scale_value(130, scale, 80, 280),
            height=self.scale_value(44, scale, 30, 88),
            corner_radius=self.scale_value(8, scale, 6, 18),
        )

        icon_sz = sz["audio_icon"]
        if self.menu_icon:
            self.menu_icon.configure(size=(icon_sz, icon_sz))

        for icon in (self.audio_icon_on, self.audio_icon_off):
            if icon:
                icon.configure(size=(icon_sz, icon_sz))

        self._safe_config(
            self.audio_toggle_btn,
            width=sz["audio_button_width"],
            height=sz["audio_button_height"],
            corner_radius=self.scale_value(8, scale, 6, 16),
        )

    def update_question_container(self):
        sz = self.size_state
        self._safe_grid(
            self.question_container,
            padx=sz["container_pad_x"],
            pady=(sz["container_pad_y"], 0),
        )
        self._safe_config(
            self.question_container, corner_radius=sz["container_corner_radius"]
        )

        self.update_image()
        self.update_definition()
        self.update_answer_boxes()

    def update_image(self):
        sz = self.size_state
        scale = sz.get("scale", 1.0)
        is_compact = sz.get("is_height_constrained", False)
        img_sz = sz["image_size"]

        self._safe_config(self.image_frame, height=img_sz)
        if self.image_frame and self.image_frame.winfo_exists():
            pt = (
                self.scale_value(12, scale, 6, 20)
                if is_compact
                else self.scale_value(24, scale, 12, 60)
            )
            pb = (
                self.scale_value(6, scale, 3, 10)
                if is_compact
                else self.scale_value(12, scale, 6, 30)
            )
            self.image_frame.grid_configure(pady=(pt, pb))

        self._safe_config(self.image_label, width=img_sz, height=img_sz)

        if self.current_image and self.current_question:
            nuevo_tam = sz.get("image_size", img_sz)
            tam_actual = getattr(self, "ultimo_tam_imagen", 0)
            if abs(nuevo_tam - tam_actual) > 2:
                self.ultimo_tam_imagen = nuevo_tam
                self.load_question_image()

    def update_definition(self):
        sz = self.size_state
        scale = sz.get("scale", 1.0)

        pad_x = sz.get("definition_pad_x", self.scale_value(36, scale, 20, 80))
        pad_y = sz.get("definition_pad_y", self.scale_value(14, scale, 8, 36))
        self._safe_grid(self.definition_frame, padx=pad_x, pady=pad_y)

        max_height = sz.get("definition_height")
        if max_height is None:
            if sz.get("is_height_constrained", False):
                max_height = self.scale_value(42, scale, 38, 50)
            else:
                max_height = (
                    self.scale_value(70, scale, 50, 110)
                    if sz.get("window_height", 0) >= 1080
                    else self.scale_value(50, scale, 42, 65)
                )
        self._safe_config(self.definition_scroll_wrapper, height=max_height)
        self._safe_config(self.definition_label, wraplength=sz["definition_wrap"])

        if self.info_icon:
            isz = sz["info_icon"]
            self.info_icon.configure(size=(isz, isz))

        self.queue_definition_scroll_update()

    def update_answer_boxes(self):
        sz = self.size_state
        scale = sz.get("scale", 1.0)
        is_compact = sz.get("is_height_constrained", False)
        box_sz, gap = sz["answer_box"], sz["answer_box_gap"]
        extra_pad = self.scale_value(16, scale, 8, 20)

        visible_boxes = [b for b in self.answer_box_labels if b.winfo_manager()]
        for box in visible_boxes:
            self._safe_config(box, width=box_sz, height=box_sz)
            self._safe_grid(box, padx=gap, pady=4)

        if visible_boxes:
            self._safe_config(
                self.answer_boxes_frame,
                width=len(visible_boxes) * (box_sz + gap * 2),
                height=box_sz + extra_pad,
            )
            pad_y = (
                self.scale_value(8, scale, 6, 12)
                if is_compact
                else self.scale_value(14, scale, 8, 28)
            )
            self._safe_grid(self.answer_boxes_frame, pady=(pad_y, pad_y // 2))

    def update_nav_buttons(self, scale):
        sz = self.size_state
        bw, bh = sz["action_button_width"], sz["action_button_height"]
        bgap, cr = sz["action_button_gap"] * 2, sz["action_corner_radius"]

        for btn in [self.prev_button, self.next_button]:
            self._safe_config(btn, width=bw, height=bh, corner_radius=cr)
            self._safe_grid(btn, padx=bgap // 2)

        pad_y = self.scale_value(16, scale, 8, 32)
        self._safe_grid(self.nav_buttons_frame, pady=(pad_y, pad_y))

        if self.bottom_container and self.bottom_container.winfo_exists():
            ks = sz.get("keyboard_scale", 1.0)
            kh = 3 * (
                max(1, int(round(sz["key_size"] * ks)))
                + max(0, int(round(sz["key_row_gap"] * ks))) * 2
            ) + max(0, int(round(sz["keyboard_pad_y"] * ks)))
            self.bottom_container.configure(
                height=kh
                + sz["action_button_height"]
                + self.scale_value(24, scale, 12, 48)
            )
            self.bottom_container.grid_propagate(False)

    def set_definition_text(self, text):
        if self.definition_label and self.definition_label.winfo_exists():
            self.definition_label.configure(text=text)
        self.queue_definition_scroll_update()

    def queue_definition_scroll_update(self):
        if not self.parent or not self.parent.winfo_exists():
            return
        self._cancel_job("definition_scroll_update_job")
        self._cancel_job("definition_scroll_delayed_job")
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

        content = (
            self.def_inner
            if self.def_inner and self.def_inner.winfo_exists()
            else (
                self.definition_label
                if self.definition_label and self.definition_label.winfo_exists()
                else None
            )
        )
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

        self.set_definition_scrollbar_visible(content_height > wrapper_height)

    def set_definition_scrollbar_visible(self, visible):
        if self.definition_scrollbar_visible is visible:
            return

        scrollbar = self._get_scrollbar_widget(self.definition_scroll)
        if not scrollbar or not scrollbar.winfo_exists():
            return

        manager = (
            self.definition_scrollbar_manager or scrollbar.winfo_manager() or "grid"
        )
        self.definition_scrollbar_manager = manager

        action_name = (
            manager
            if visible
            else (
                f"{manager}_forget" if manager in ("pack", "place") else "grid_remove"
            )
        )
        action = getattr(scrollbar, action_name, None)
        if action:
            action()

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

        for job_attr in (
            "resize_job",
            "definition_scroll_update_job",
            "definition_scroll_delayed_job",
        ):
            self._cancel_job(job_attr)

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

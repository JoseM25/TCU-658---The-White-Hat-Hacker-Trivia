import os
import json
import random
import customtkinter as ctk
from PIL import Image, ImageTk
from tksvg import SvgImage as TkSvgImage

from juego.tts_service import TTSService


class GameScreen:

    BASE_DIMENSIONS = (1280, 720)
    BASE_FONT_SIZES = {
        "timer": 24,
        "score": 28,
        "definition": 16,
        "keyboard": 18,
        "answer_box": 20,
        "button": 20,
        "header_label": 14,
    }
    SCALE_LIMITS = (0.50, 1.60)
    RESIZE_DELAY = 80
    SVG_RASTER_SCALE = 2.0
    AUDIO_ICON_BASE_SIZE = 36
    AUDIO_ICON_MIN_SIZE = 28
    AUDIO_ICON_MAX_SIZE = 48
    DELETE_ICON_BASE_SIZE = 26

    BASE_IMAGE_SIZE = 180
    IMAGE_MIN_SIZE = 100
    IMAGE_MAX_SIZE = 280

    BASE_KEY_SIZE = 44
    KEY_MIN_SIZE = 32
    KEY_MAX_SIZE = 60

    BASE_ANSWER_BOX_SIZE = 40
    ANSWER_BOX_MIN_SIZE = 28
    ANSWER_BOX_MAX_SIZE = 56

    COLORS = {
        "primary_blue": "#005DFF",
        "primary_hover": "#003BB8",
        "success_green": "#00CFC5",
        "success_hover": "#009B94",
        "warning_yellow": "#FFC553",
        "warning_hover": "#CC9A42",
        "danger_red": "#FF4F60",
        "danger_hover": "#CC3F4D",
        "text_dark": "#202632",
        "text_medium": "#3A3F4B",
        "text_light": "#7A7A7A",
        "bg_light": "#F5F7FA",
        "bg_card": "#FFFFFF",
        "border_light": "#E2E7F3",
        "border_medium": "#D3DBEA",
        "header_bg": "#202632",
        "header_hover": "#273246",
        "key_bg": "#E8ECF2",
        "key_hover": "#D0D6E0",
        "key_pressed": "#B8C0D0",
        "answer_box_empty": "#E2E7F3",
        "answer_box_filled": "#D0D6E0",
    }

    KEYBOARD_LAYOUT = [
        ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
        ["A", "S", "D", "F", "G", "H", "J", "K", "L"],
        ["Z", "X", "C", "V", "B", "N", "M", "⌫"],
    ]

    def __init__(self, parent, on_return_callback=None, tts_service=None):
        self.parent = parent
        self.on_return_callback = on_return_callback

        self.current_question = None
        self.questions = []
        self.available_questions = []
        self.score = 0
        self.current_answer = ""
        self.timer_seconds = 0
        self.audio_enabled = True
        self.timer_running = False
        self.timer_job = None

        self.resize_job = None
        self.main = None
        self.header_frame = None
        self.back_button = None
        self.back_arrow_icon = None
        self.timer_label = None
        self.score_label = None
        self.audio_toggle_btn = None
        self.question_container = None
        self.image_label = None
        self.definition_label = None
        self.answer_boxes_frame = None
        self.answer_box_labels = []
        self.keyboard_frame = None
        self.keyboard_buttons = []
        self.delete_button = None
        self.action_buttons_frame = None
        self.skip_button = None
        self.check_button = None
        self.current_image = None
        self.audio_icon_on = None
        self.audio_icon_off = None
        self.clock_icon = None
        self.star_icon = None
        self.delete_icon = None
        self.timer_icon_label = None
        self.star_icon_label = None
        self.wildcards_frame = None
        self.wildcard_x2_btn = None
        self.wildcard_hint_btn = None
        self.wildcard_freeze_btn = None
        self.info_icon = None
        self.info_icon_label = None

        self.images_dir = os.path.join("recursos", "imagenes")
        self.audio_dir = os.path.join("recursos", "audio")
        self.questions_path = os.path.join("datos", "preguntas.json")

        self.tts = tts_service or TTSService(self.audio_dir)

        self.create_fonts()

        self.load_questions()
        self.build_ui()

        self.parent.bind("<Configure>", self.on_resize)
        self.apply_responsive()

        self.load_random_question()
        self.start_timer()

    def create_fonts(self):
        self.timer_font = ctk.CTkFont(
            family="Poppins SemiBold",
            size=self.BASE_FONT_SIZES["timer"],
            weight="bold",
        )
        self.score_font = ctk.CTkFont(
            family="Poppins ExtraBold",
            size=self.BASE_FONT_SIZES["score"],
            weight="bold",
        )
        self.definition_font = ctk.CTkFont(
            family="Open Sans Regular",
            size=self.BASE_FONT_SIZES["definition"],
        )
        self.keyboard_font = ctk.CTkFont(
            family="Poppins SemiBold",
            size=self.BASE_FONT_SIZES["keyboard"],
            weight="bold",
        )
        self.answer_box_font = ctk.CTkFont(
            family="Poppins ExtraBold",
            size=self.BASE_FONT_SIZES["answer_box"],
            weight="bold",
        )
        self.button_font = ctk.CTkFont(
            family="Poppins SemiBold",
            size=self.BASE_FONT_SIZES["button"],
        )
        self.header_button_font = ctk.CTkFont(
            family="Poppins SemiBold",
            size=20,
            weight="bold",
        )
        self.header_label_font = ctk.CTkFont(
            family="Poppins SemiBold",
            size=self.BASE_FONT_SIZES["header_label"],
        )

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

        self.main = ctk.CTkFrame(self.parent, fg_color="transparent")
        self.main.grid(row=0, column=0, sticky="nsew")

        self.main.grid_rowconfigure(0, weight=0)
        self.main.grid_rowconfigure(1, weight=1)
        self.main.grid_rowconfigure(2, weight=0)
        self.main.grid_rowconfigure(3, weight=0)
        self.main.grid_columnconfigure(0, weight=1)

        self.build_header()
        self.build_question_container()
        self.build_keyboard()
        self.build_action_buttons()

    def build_header(self):
        self.header_frame = ctk.CTkFrame(
            self.main,
            fg_color=self.COLORS["header_bg"],
            height=60,
            corner_radius=0,
        )
        self.header_frame.grid(row=0, column=0, sticky="ew")
        self.header_frame.grid_propagate(False)

        self.header_frame.grid_columnconfigure(0, weight=1)
        self.header_frame.grid_columnconfigure(1, weight=0)
        self.header_frame.grid_columnconfigure(2, weight=1)
        self.header_frame.grid_rowconfigure(0, weight=1)

        left_container = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        left_container.grid(row=0, column=0, sticky="w", padx=(0, 0))

        self.load_header_icons()

        self.back_button = ctk.CTkButton(
            left_container,
            text="Menu",
            image=self.back_arrow_icon,
            compound="left",
            anchor="w",
            font=self.header_button_font,
            width=96,
            height=40,
            fg_color="transparent",
            hover_color=self.COLORS["header_hover"],
            text_color="white",
            corner_radius=8,
            command=self.return_to_menu,
        )
        self.back_button.grid(row=0, column=0, padx=(0, 16))

        timer_container = ctk.CTkFrame(left_container, fg_color="transparent")
        timer_container.grid(row=0, column=1, padx=(8, 0))

        self.timer_icon_label = ctk.CTkLabel(
            timer_container,
            text="",
            image=self.clock_icon,
        )
        self.timer_icon_label.grid(row=0, column=0, padx=(0, 8))

        self.timer_label = ctk.CTkLabel(
            timer_container,
            text="00:00",
            font=self.timer_font,
            text_color="white",
        )
        self.timer_label.grid(row=0, column=1)

        score_container = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        score_container.grid(row=0, column=1)

        self.star_icon_label = ctk.CTkLabel(
            score_container,
            text="",
            image=self.star_icon,
        )
        self.star_icon_label.grid(row=0, column=0, padx=(0, 8))

        self.score_label = ctk.CTkLabel(
            score_container,
            text="0",
            font=self.score_font,
            text_color="white",
        )
        self.score_label.grid(row=0, column=1)

        audio_container = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        audio_container.grid(row=0, column=2, sticky="e", padx=(0, 24))

        self.load_audio_icons()

        self.audio_toggle_btn = ctk.CTkButton(
            audio_container,
            text="",
            image=self.audio_icon_on,
            font=self.timer_font,
            width=48,
            height=40,
            fg_color="transparent",
            hover_color=self.COLORS["header_hover"],
            text_color="white",
            corner_radius=8,
            command=self.toggle_audio,
        )
        self.audio_toggle_btn.grid(row=0, column=0)
        self.update_audio_button_icon()

    def load_header_icons(self):

        arrow_svg_path = os.path.join(self.images_dir, "arrow.svg")
        try:
            img = self.load_svg_image(arrow_svg_path, scale=self.SVG_RASTER_SCALE)
            if img:
                self.back_arrow_icon = ctk.CTkImage(
                    light_image=img, dark_image=img, size=(20, 20)
                )
        except (FileNotFoundError, OSError, ValueError):
            self.back_arrow_icon = None

        clock_svg_path = os.path.join(self.images_dir, "clock.svg")
        try:
            img = self.load_svg_image(clock_svg_path, scale=self.SVG_RASTER_SCALE)
            if img:
                self.clock_icon = ctk.CTkImage(
                    light_image=img, dark_image=img, size=(24, 24)
                )
        except (FileNotFoundError, OSError, ValueError):
            self.clock_icon = None

        star_svg_path = os.path.join(self.images_dir, "star.svg")
        try:
            img = self.load_svg_image(star_svg_path, scale=self.SVG_RASTER_SCALE)
            if img:
                self.star_icon = ctk.CTkImage(
                    light_image=img, dark_image=img, size=(24, 24)
                )
        except (FileNotFoundError, OSError, ValueError):
            self.star_icon = None

    def load_audio_icons(self):
        self.audio_icon_on = None
        self.audio_icon_off = None

        icon_size = self.calculate_audio_icon_size(scale=1.0)

        icon_specs = [
            ("audio_icon_on", "volume-white.svg"),
            ("audio_icon_off", "volume-mute.svg"),
        ]

        for attr, filename in icon_specs:
            svg_path = os.path.join(self.images_dir, filename)
            try:
                img = self.load_svg_image(svg_path, scale=self.SVG_RASTER_SCALE)
                if img:
                    setattr(
                        self,
                        attr,
                        ctk.CTkImage(
                            light_image=img,
                            dark_image=img,
                            size=(icon_size, icon_size),
                        ),
                    )
            except (FileNotFoundError, OSError, ValueError):
                setattr(self, attr, None)

    def calculate_audio_icon_size(self, scale, back_height=None):
        base_scaled = self.AUDIO_ICON_BASE_SIZE * scale
        size_targets = [
            base_scaled,
            self.timer_font.cget("size"),
            self.score_font.cget("size"),
        ]
        if back_height:
            size_targets.append(back_height * 0.85)
        target_size = max(size_targets)
        return int(
            max(
                self.AUDIO_ICON_MIN_SIZE,
                min(self.AUDIO_ICON_MAX_SIZE, target_size),
            )
        )

    def update_audio_icon_size(self, icon_size, back_height=None, corner_radius=None):
        for icon in (self.audio_icon_on, self.audio_icon_off):
            if icon:
                icon.configure(size=(icon_size, icon_size))

        if not self.audio_toggle_btn:
            return

        current_width = int(self.audio_toggle_btn.cget("width"))
        current_height = int(self.audio_toggle_btn.cget("height"))

        audio_height = max(current_height, int(icon_size + 8), int(back_height or 0))
        audio_width = max(current_width, int(icon_size + 12), audio_height)

        kwargs = {
            "width": audio_width,
            "height": audio_height,
        }
        if corner_radius is not None:
            kwargs["corner_radius"] = corner_radius

        self.audio_toggle_btn.configure(**kwargs)

    def update_audio_button_icon(self):
        if not self.audio_toggle_btn:
            return

        icon = self.audio_icon_on if self.audio_enabled else self.audio_icon_off
        if icon:
            self.audio_toggle_btn.configure(image=icon, text="")
        else:
            fallback_text = "On" if self.audio_enabled else "Off"
            self.audio_toggle_btn.configure(image=None, text=fallback_text)

    def load_info_icon(self):
        info_svg_path = os.path.join(self.images_dir, "info.svg")
        try:
            img = self.load_svg_image(info_svg_path, scale=self.SVG_RASTER_SCALE)
            if img:
                self.info_icon = ctk.CTkImage(
                    light_image=img, dark_image=img, size=(24, 24)
                )
        except (FileNotFoundError, OSError, ValueError):
            self.info_icon = None

    def load_delete_icon(self):
        delete_svg_path = os.path.join(self.images_dir, "delete.svg")
        try:
            img = self.load_svg_image(delete_svg_path, scale=self.SVG_RASTER_SCALE)
            if img:
                icon_size = self.calculate_delete_icon_size(self.BASE_KEY_SIZE)
                self.delete_icon = ctk.CTkImage(
                    light_image=img,
                    dark_image=img,
                    size=(icon_size, icon_size),
                )
        except (FileNotFoundError, OSError, ValueError):
            self.delete_icon = None

    def calculate_delete_icon_size(self, key_size):
        scale_factor = self.DELETE_ICON_BASE_SIZE / self.BASE_KEY_SIZE
        target_size = key_size * scale_factor
        return int(max(16, min(40, target_size)))

    def update_delete_icon_size(self, key_size):
        if not self.delete_icon:
            return
        icon_size = self.calculate_delete_icon_size(key_size)
        self.delete_icon.configure(size=(icon_size, icon_size))

    def build_question_container(self):

        self.question_container = ctk.CTkFrame(
            self.main,
            fg_color=self.COLORS["bg_card"],
            corner_radius=20,
            border_width=2,
            border_color=self.COLORS["border_light"],
        )
        self.question_container.grid(row=1, column=0, sticky="nsew", padx=40, pady=20)

        self.question_container.grid_columnconfigure(0, weight=1)
        self.question_container.grid_columnconfigure(1, weight=0)
        self.question_container.grid_rowconfigure(0, weight=1)

        content_frame = ctk.CTkFrame(self.question_container, fg_color="transparent")
        content_frame.grid(row=0, column=0, sticky="nsew")
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(0, weight=0)
        content_frame.grid_rowconfigure(1, weight=1)
        content_frame.grid_rowconfigure(2, weight=0)

        image_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        image_frame.grid(row=0, column=0, pady=(20, 10))

        self.image_label = ctk.CTkLabel(
            image_frame,
            text="",
            fg_color=self.COLORS["bg_light"],
            corner_radius=16,
            width=self.BASE_IMAGE_SIZE,
            height=self.BASE_IMAGE_SIZE,
        )
        self.image_label.grid(row=0, column=0)

        definition_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        definition_frame.grid(row=1, column=0, sticky="nsew", padx=30, pady=10)
        definition_frame.grid_columnconfigure(0, weight=1)
        definition_frame.grid_rowconfigure(0, weight=1)

        self.load_info_icon()

        definition_inner = ctk.CTkFrame(definition_frame, fg_color="transparent")
        definition_inner.grid(row=0, column=0, sticky="")

        self.info_icon_label = ctk.CTkLabel(
            definition_inner,
            text="",
            image=self.info_icon,
        )
        self.info_icon_label.grid(row=0, column=0, sticky="n", padx=(0, 8), pady=(2, 0))

        self.definition_label = ctk.CTkLabel(
            definition_inner,
            text="Loading question...",
            font=self.definition_font,
            text_color=self.COLORS["text_medium"],
            wraplength=600,
            justify="left",
            anchor="w",
        )
        self.definition_label.grid(row=0, column=1, sticky="w")

        self.answer_boxes_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        self.answer_boxes_frame.grid(row=2, column=0, pady=(10, 24))

        self.build_wildcards_panel()

    def build_wildcards_panel(self):

        self.wildcards_frame = ctk.CTkFrame(
            self.question_container,
            fg_color="transparent",
        )
        self.wildcards_frame.grid(row=0, column=1, sticky="ns", padx=(0, 24), pady=24)

        self.wildcards_frame.grid_rowconfigure(0, weight=1)
        self.wildcards_frame.grid_rowconfigure(4, weight=1)

        wildcard_size = 56
        wildcard_font_size = 18

        self.wildcard_x2_btn = ctk.CTkButton(
            self.wildcards_frame,
            text="X2",
            font=ctk.CTkFont(
                family="Poppins ExtraBold", size=wildcard_font_size, weight="bold"
            ),
            width=wildcard_size,
            height=wildcard_size,
            corner_radius=wildcard_size,
            fg_color="#FFC553",
            hover_color="#E5B04A",
            text_color="white",
            command=self.on_wildcard_x2,
        )
        self.wildcard_x2_btn.grid(row=1, column=0, pady=8)

        self.wildcard_hint_btn = ctk.CTkButton(
            self.wildcards_frame,
            text="A",
            font=ctk.CTkFont(
                family="Poppins ExtraBold", size=wildcard_font_size, weight="bold"
            ),
            width=wildcard_size,
            height=wildcard_size,
            corner_radius=wildcard_size,
            fg_color="#00CFC5",
            hover_color="#00B5AD",
            text_color="white",
            command=self.on_wildcard_hint,
        )
        self.wildcard_hint_btn.grid(row=2, column=0, pady=8)

        self.wildcard_freeze_btn = ctk.CTkButton(
            self.wildcards_frame,
            text="❄",
            font=ctk.CTkFont(family="Segoe UI Emoji", size=wildcard_font_size),
            width=wildcard_size,
            height=wildcard_size,
            corner_radius=wildcard_size,
            fg_color="#005DFF",
            hover_color="#0048CC",
            text_color="white",
            command=self.on_wildcard_freeze,
        )
        self.wildcard_freeze_btn.grid(row=3, column=0, pady=8)

    def on_wildcard_x2(self):
        print("X2 wildcard activated")

    def on_wildcard_hint(self):
        print("Hint wildcard activated")

    def on_wildcard_freeze(self):
        print("Freeze wildcard activated")

    def build_keyboard(self):
        self.keyboard_frame = ctk.CTkFrame(
            self.main,
            fg_color="transparent",
        )
        self.keyboard_frame.grid(row=2, column=0, pady=(0, 16))

        self.keyboard_buttons.clear()
        self.delete_button = None
        self.load_delete_icon()

        for row_idx, row_keys in enumerate(self.KEYBOARD_LAYOUT):
            row_frame = ctk.CTkFrame(self.keyboard_frame, fg_color="transparent")
            row_frame.grid(row=row_idx, column=0, pady=4)

            for col_idx, key in enumerate(row_keys):

                if key == "⌫":
                    width = int(self.BASE_KEY_SIZE * 1.8)
                    fg_color = self.COLORS["danger_red"]
                    hover_color = self.COLORS["danger_hover"]
                    text_color = "white"
                    btn_image = self.delete_icon
                    btn_text = "" if btn_image else key
                else:
                    width = self.BASE_KEY_SIZE
                    fg_color = self.COLORS["key_bg"]
                    hover_color = self.COLORS["key_hover"]
                    text_color = self.COLORS["text_dark"]
                    btn_image = None
                    btn_text = key

                btn = ctk.CTkButton(
                    row_frame,
                    text=btn_text,
                    image=btn_image,
                    font=self.keyboard_font,
                    width=width,
                    height=self.BASE_KEY_SIZE,
                    fg_color=fg_color,
                    hover_color=hover_color,
                    text_color=text_color,
                    corner_radius=8,
                    command=lambda k=key: self.on_key_press(k),
                )
                btn.grid(row=0, column=col_idx, padx=3)
                self.keyboard_buttons.append(btn)
                if key == "⌫":
                    self.delete_button = btn

    def build_action_buttons(self):
        self.action_buttons_frame = ctk.CTkFrame(self.main, fg_color="transparent")
        self.action_buttons_frame.grid(row=3, column=0, pady=(0, 24))

        self.skip_button = ctk.CTkButton(
            self.action_buttons_frame,
            text="Skip",
            font=self.button_font,
            width=140,
            height=48,
            fg_color=self.COLORS["bg_light"],
            hover_color=self.COLORS["border_medium"],
            text_color="black",
            border_width=2,
            border_color="black",
            corner_radius=12,
            command=self.on_skip,
        )
        self.skip_button.grid(row=0, column=0, padx=16)

        self.check_button = ctk.CTkButton(
            self.action_buttons_frame,
            text="Check",
            font=self.button_font,
            width=140,
            height=48,
            fg_color="#005DFF",
            hover_color="#003BB8",
            text_color="white",
            corner_radius=12,
            command=self.on_check,
        )
        self.check_button.grid(row=0, column=1, padx=16)

    def create_answer_boxes(self, word_length):

        for widget in self.answer_boxes_frame.winfo_children():
            widget.destroy()
        self.answer_box_labels.clear()

        for i in range(word_length):
            box = ctk.CTkLabel(
                self.answer_boxes_frame,
                text="",
                font=self.answer_box_font,
                width=self.BASE_ANSWER_BOX_SIZE,
                height=self.BASE_ANSWER_BOX_SIZE,
                fg_color=self.COLORS["answer_box_empty"],
                corner_radius=8,
                text_color=self.COLORS["text_dark"],
            )
            box.grid(row=0, column=i, padx=3)
            self.answer_box_labels.append(box)

    def load_random_question(self):

        self.tts.stop()

        if not self.questions:
            self.definition_label.configure(text="No questions available!")
            return

        if not self.available_questions:
            self.available_questions = list(self.questions)

        self.current_question = random.choice(self.available_questions)

        self.available_questions.remove(self.current_question)

        self.current_answer = ""
        self.timer_seconds = 0

        definition = self.current_question.get("definition", "No definition")
        self.definition_label.configure(text=definition)

        title = self.current_question.get("title", "")

        clean_title = title.replace(" ", "")
        self.create_answer_boxes(len(clean_title))

        self.load_question_image()

        if self.audio_enabled and definition and definition != "No definition":
            self.tts.speak(definition)

    def load_question_image(self):
        if not self.current_question:
            return

        image_path = self.current_question.get("image", "")
        if not image_path:
            self.image_label.configure(image=None, text="No Image")
            return

        try:

            if not os.path.isabs(image_path):
                image_path = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)), image_path
                )

            if os.path.exists(image_path):
                pil_image = Image.open(image_path).convert("RGBA")

                width, height = pil_image.size
                max_size = self.BASE_IMAGE_SIZE
                scale = min(max_size / width, max_size / height)
                new_width = int(width * scale)
                new_height = int(height * scale)

                self.current_image = ctk.CTkImage(
                    light_image=pil_image,
                    dark_image=pil_image,
                    size=(new_width, new_height),
                )
                self.image_label.configure(
                    image=self.current_image,
                    text="",
                    width=max_size,
                    height=max_size,
                )
            else:
                self.image_label.configure(image=None, text="Image not found")
        except (FileNotFoundError, OSError, ValueError) as e:
            print(f"Error loading image: {e}")
            self.image_label.configure(image=None, text="Error loading image")

    def on_key_press(self, key):
        if not self.current_question:
            return

        title = self.current_question.get("title", "")
        clean_title = title.replace(" ", "")
        max_length = len(clean_title)

        if key == "⌫":

            if self.current_answer:
                self.current_answer = self.current_answer[:-1]
        else:

            if len(self.current_answer) < max_length:
                self.current_answer += key

        self.update_answer_boxes()

    def update_answer_boxes(self):
        for i, box in enumerate(self.answer_box_labels):
            if i < len(self.current_answer):
                box.configure(
                    text=self.current_answer[i],
                    fg_color=self.COLORS["answer_box_filled"],
                )
            else:
                box.configure(
                    text="",
                    fg_color=self.COLORS["answer_box_empty"],
                )

    def toggle_audio(self):
        self.audio_enabled = not self.audio_enabled
        self.update_audio_button_icon()
        if self.audio_enabled:
            if self.current_question:
                definition = self.current_question.get("definition", "").strip()
                if definition:
                    self.tts.speak(definition)
        else:
            self.tts.stop()

    def on_skip(self):
        print("Skip pressed")
        self.load_random_question()

    def on_check(self):
        if not self.current_question:
            return

        title = self.current_question.get("title", "")
        clean_title = title.replace(" ", "").upper()
        user_answer = self.current_answer.upper()

        if user_answer == clean_title:
            print("Correct!")
            self.score += 100
            self.score_label.configure(text=str(self.score))
            self.load_random_question()
        else:
            print(f"Incorrect! Expected: {clean_title}, Got: {user_answer}")

    def start_timer(self):
        self.timer_running = True
        self.update_timer()

    def stop_timer(self):
        self.timer_running = False
        if self.timer_job:
            self.parent.after_cancel(self.timer_job)
            self.timer_job = None

    def update_timer(self):
        if not self.timer_running:
            return

        self.timer_seconds += 1
        minutes = self.timer_seconds // 60
        seconds = self.timer_seconds % 60
        self.timer_label.configure(text=f"{minutes:02d}:{seconds:02d}")

        self.timer_job = self.parent.after(1000, self.update_timer)

    def on_resize(self, event):
        if event.widget is not self.parent:
            return

        if self.resize_job:
            self.parent.after_cancel(self.resize_job)
        self.resize_job = self.parent.after(self.RESIZE_DELAY, self.apply_responsive)

    def apply_responsive(self):
        width = max(self.parent.winfo_width(), 1)
        height = max(self.parent.winfo_height(), 1)

        scale = min(width / self.BASE_DIMENSIONS[0], height / self.BASE_DIMENSIONS[1])
        scale = max(self.SCALE_LIMITS[0], min(self.SCALE_LIMITS[1], scale))

        self.timer_font.configure(
            size=int(max(14, self.BASE_FONT_SIZES["timer"] * scale))
        )
        self.score_font.configure(
            size=int(max(16, self.BASE_FONT_SIZES["score"] * scale))
        )
        self.definition_font.configure(
            size=int(max(12, self.BASE_FONT_SIZES["definition"] * scale))
        )
        self.keyboard_font.configure(
            size=int(max(12, self.BASE_FONT_SIZES["keyboard"] * scale))
        )
        self.answer_box_font.configure(
            size=int(max(14, self.BASE_FONT_SIZES["answer_box"] * scale))
        )
        self.button_font.configure(
            size=int(max(12, self.BASE_FONT_SIZES["button"] * scale))
        )
        self.header_button_font.configure(size=int(max(12, min(32, 20 * scale))))
        self.header_label_font.configure(
            size=int(max(10, self.BASE_FONT_SIZES["header_label"] * scale))
        )

        def clamp_scaled(base, min_value, max_value):
            return int(max(min_value, min(max_value, base * scale)))

        pad_top = clamp_scaled(28, 12, 64)
        pad_bottom = clamp_scaled(32, 14, 72)
        pad_left = clamp_scaled(24, 10, 60)
        pad_right = clamp_scaled(16, 8, 48)
        back_width = clamp_scaled(96, 70, 170)
        back_height = clamp_scaled(40, 30, 64)
        back_corner = clamp_scaled(8, 6, 16)

        header_height = max(
            back_height + pad_top + pad_bottom, int(max(48, 60 * scale))
        )
        self.header_frame.configure(height=header_height)

        if self.back_button:
            self.back_button.grid_configure(
                padx=(pad_left, pad_right), pady=(pad_top, pad_bottom)
            )
            self.back_button.configure(
                width=back_width, height=back_height, corner_radius=back_corner
            )

        audio_icon_size = self.calculate_audio_icon_size(scale, back_height)
        self.update_audio_icon_size(audio_icon_size, back_height, back_corner)

        image_size = int(
            max(
                self.IMAGE_MIN_SIZE,
                min(self.IMAGE_MAX_SIZE, self.BASE_IMAGE_SIZE * scale),
            )
        )
        self.image_label.configure(width=image_size, height=image_size)

        if self.current_image and self.current_question:
            self.load_question_image()

        wrap_length = int(max(300, min(800, 600 * scale)))
        self.definition_label.configure(wraplength=wrap_length)

        box_size = int(
            max(
                self.ANSWER_BOX_MIN_SIZE,
                min(self.ANSWER_BOX_MAX_SIZE, self.BASE_ANSWER_BOX_SIZE * scale),
            )
        )
        for box in self.answer_box_labels:
            box.configure(width=box_size, height=box_size)

        key_size = int(
            max(
                self.KEY_MIN_SIZE,
                min(self.KEY_MAX_SIZE, self.BASE_KEY_SIZE * scale),
            )
        )
        for btn in self.keyboard_buttons:
            is_delete_key = btn is self.delete_button
            if is_delete_key:
                btn.configure(width=int(key_size * 1.8), height=key_size)
                self.update_delete_icon_size(key_size)
            else:
                btn.configure(width=key_size, height=key_size)

        button_width = int(max(100, 140 * scale))
        button_height = int(max(36, 48 * scale))
        self.skip_button.configure(width=button_width, height=button_height)
        self.check_button.configure(width=button_width, height=button_height)

        container_padx = int(max(20, 40 * scale))
        container_pady = int(max(12, 20 * scale))
        self.question_container.grid_configure(padx=container_padx, pady=container_pady)

        self.resize_job = None

    def load_svg_image(self, svg_path, scale=1.0):
        try:
            svg_photo = TkSvgImage(file=str(svg_path), scale=scale)
            pil = ImageTk.getimage(svg_photo).convert("RGBA")
            return pil
        except (FileNotFoundError, ValueError) as e:
            print(f"Error loading SVG image '{svg_path}': {e}")
            return None

    def return_to_menu(self):
        self.stop_timer()
        self.tts.stop()
        if self.on_return_callback:
            self.on_return_callback()

    def cleanup(self):
        self.stop_timer()
        self.tts.stop()
        self.parent.unbind("<Configure>")

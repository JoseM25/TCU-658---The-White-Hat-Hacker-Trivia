import json
import os

import customtkinter as ctk
from PIL import ImageTk
from tksvg import SvgImage as TkSvgImage

from juego.comodines import WildcardManager
from juego.logica import ScoringSystem
from juego.tts_service import TTSService


class GameScreenBase:
    BASE_DIMENSIONS = (1280, 720)
    BASE_FONT_SIZES = {
        "timer": 24,
        "score": 28,
        "definition": 16,
        "keyboard": 18,
        "answer_box": 20,
        "button": 20,
        "header_label": 14,
        "feedback": 14,
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
        "feedback_correct": "#00CFC5",
        "feedback_incorrect": "#FF4F60",
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
        self.questions_answered = 0
        self.game_completed = False
        self.completion_modal = None
        self.scoring_system = None
        self.wildcard_manager = WildcardManager()
        self.question_timer = 0
        self.question_mistakes = 0
        self.resize_job = None
        self.main = None
        self.header_frame = None
        self.header_left_container = None
        self.header_center_container = None
        self.header_right_container = None
        self.back_button = None
        self.back_arrow_icon = None
        self.timer_container = None
        self.score_container = None
        self.audio_container = None
        self.timer_label = None
        self.score_label = None
        self.audio_toggle_btn = None
        self.question_container = None
        self.image_frame = None
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
        self.freeze_icon = None
        self.timer_frozen_visually = False
        self.wildcards_frame = None
        self.wildcard_x2_btn = None
        self.wildcard_hint_btn = None
        self.wildcard_freeze_btn = None
        self.charges_frame = None
        self.charges_label = None
        self.lightning_icon = None
        self.lightning_icon_label = None
        self.info_icon = None
        self.info_icon_label = None
        self.feedback_label = None
        self.feedback_animation_job = None
        self.skip_modal = None
        self.summary_modal = None
        self.processing_correct_answer = False
        self.awaiting_modal_decision = False
        self.stored_modal_data = None
        self.question_history = []
        self.viewing_history_index = -1
        self.images_dir = os.path.join("recursos", "imagenes")
        self.audio_dir = os.path.join("recursos", "audio")
        self.questions_path = os.path.join("datos", "preguntas.json")
        self.tts = tts_service or TTSService(self.audio_dir)
        self.key_button_map = {}
        self.physical_key_pressed = None
        self.key_feedback_job = None

        self.create_fonts()
        self.load_questions()
        self.build_ui()

    def create_fonts(self):
        self.timer_font = ctk.CTkFont(
            family="Poppins SemiBold", size=self.BASE_FONT_SIZES["timer"], weight="bold"
        )
        self.score_font = ctk.CTkFont(
            family="Poppins ExtraBold",
            size=self.BASE_FONT_SIZES["score"],
            weight="bold",
        )
        self.definition_font = ctk.CTkFont(
            family="Open Sans Regular", size=self.BASE_FONT_SIZES["definition"]
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
            family="Poppins SemiBold", size=self.BASE_FONT_SIZES["button"]
        )
        self.header_button_font = ctk.CTkFont(
            family="Poppins SemiBold", size=20, weight="bold"
        )
        self.header_label_font = ctk.CTkFont(
            family="Poppins SemiBold", size=self.BASE_FONT_SIZES["header_label"]
        )
        self.feedback_font = ctk.CTkFont(
            family="Poppins SemiBold",
            size=self.BASE_FONT_SIZES["feedback"],
            weight="bold",
        )

    def load_questions(self):
        try:
            with open(self.questions_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.questions = data.get("questions", [])
                self.available_questions = list(self.questions)
                self.scoring_system = ScoringSystem(len(self.questions))
                # Reset wildcard manager for new game
                self.wildcard_manager.reset_game()
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading questions: {e}")
            self.questions = []
            self.available_questions = []
            self.scoring_system = ScoringSystem(1)
            self.wildcard_manager.reset_game()

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
            self.main, fg_color=self.COLORS["header_bg"], height=60, corner_radius=0
        )
        self.header_frame.grid(row=0, column=0, sticky="ew")
        self.header_frame.grid_propagate(False)
        # Spanned header layout:
        # - left: timer
        # - center: score (visually centered)
        # - right: mute toggle
        #
        # Use `uniform` so left/right columns share the same base width, keeping the
        # center column perfectly centered even if timer/mute have different widths.
        self.header_frame.grid_columnconfigure(0, weight=1, uniform="header_side")
        self.header_frame.grid_columnconfigure(1, weight=0)
        self.header_frame.grid_columnconfigure(2, weight=1, uniform="header_side")
        self.header_frame.grid_rowconfigure(0, weight=1)

        self.load_header_icons()

        # The Menu/back button is intentionally not shown on game screens.
        self.back_button = None

        self.header_left_container = ctk.CTkFrame(
            self.header_frame, fg_color="transparent"
        )
        self.header_left_container.grid(row=0, column=0, sticky="w", padx=(24, 0))

        self.header_center_container = ctk.CTkFrame(
            self.header_frame, fg_color="transparent"
        )
        self.header_center_container.grid(row=0, column=1)

        self.header_right_container = ctk.CTkFrame(
            self.header_frame, fg_color="transparent"
        )
        self.header_right_container.grid(row=0, column=2, sticky="e", padx=(0, 24))

        # Left: timer
        self.timer_container = ctk.CTkFrame(
            self.header_left_container, fg_color="transparent"
        )
        self.timer_container.grid(row=0, column=0)
        self.timer_icon_label = ctk.CTkLabel(
            self.timer_container, text="", image=self.clock_icon
        )
        self.timer_icon_label.grid(row=0, column=0, padx=(0, 8))
        self.timer_label = ctk.CTkLabel(
            self.timer_container, text="00:00", font=self.timer_font, text_color="white"
        )
        self.timer_label.grid(row=0, column=1)

        # Center: score (balanced so the number remains centered even with an icon)
        self.score_container = ctk.CTkFrame(
            self.header_center_container, fg_color="transparent"
        )
        self.score_container.grid(row=0, column=0)
        star_sz = 24
        self.star_icon_label = ctk.CTkLabel(
            self.score_container,
            text="",
            image=self.star_icon,
            width=star_sz,
            height=star_sz,
        )
        self.star_icon_label.grid(row=0, column=0, padx=(0, 8))
        self.score_label = ctk.CTkLabel(
            self.score_container, text="0", font=self.score_font, text_color="white"
        )
        self.score_label.grid(row=0, column=1)
        # Spacer mirrors the icon+gap so the score text stays visually centered.
        ctk.CTkLabel(self.score_container, text="", width=star_sz + 8).grid(
            row=0, column=2
        )

        # Right: mute toggle
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
        for attr, fname, sz in [
            ("back_arrow_icon", "arrow.svg", 20),
            ("clock_icon", "clock.svg", 24),
            ("star_icon", "star.svg", 24),
            ("freeze_icon", "freeze.svg", 24),
        ]:
            try:
                img = self.load_svg_image(
                    os.path.join(self.images_dir, fname), self.SVG_RASTER_SCALE
                )
                if img:
                    setattr(
                        self,
                        attr,
                        ctk.CTkImage(light_image=img, dark_image=img, size=(sz, sz)),
                    )
            except (FileNotFoundError, OSError, ValueError):
                setattr(self, attr, None)

    def load_audio_icons(self):
        self.audio_icon_on = self.audio_icon_off = None
        sz = self.calculate_audio_icon_size(1.0)
        for attr, fname in [
            ("audio_icon_on", "volume-white.svg"),
            ("audio_icon_off", "volume-mute.svg"),
        ]:
            try:
                img = self.load_svg_image(
                    os.path.join(self.images_dir, fname), self.SVG_RASTER_SCALE
                )
                if img:
                    setattr(
                        self,
                        attr,
                        ctk.CTkImage(light_image=img, dark_image=img, size=(sz, sz)),
                    )
            except (FileNotFoundError, OSError, ValueError):
                setattr(self, attr, None)

    def calculate_audio_icon_size(self, scale, back_height=None):
        targets = [
            self.AUDIO_ICON_BASE_SIZE * scale,
            self.timer_font.cget("size"),
            self.score_font.cget("size"),
        ]
        if back_height:
            targets.append(back_height * 0.85)
        return int(
            max(self.AUDIO_ICON_MIN_SIZE, min(self.AUDIO_ICON_MAX_SIZE, max(targets)))
        )

    def update_audio_icon_size(self, sz, back_height=None, corner_radius=None):
        for icon in (self.audio_icon_on, self.audio_icon_off):
            if icon:
                icon.configure(size=(sz, sz))
        if self.audio_toggle_btn:
            h = max(
                int(self.audio_toggle_btn.cget("height")), sz + 8, int(back_height or 0)
            )
            w = max(int(self.audio_toggle_btn.cget("width")), sz + 12, h)
            kw = {"width": w, "height": h}
            if corner_radius is not None:
                kw["corner_radius"] = corner_radius
            self.audio_toggle_btn.configure(**kw)

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

    def load_info_icon(self):
        try:
            img = self.load_svg_image(
                os.path.join(self.images_dir, "info.svg"), self.SVG_RASTER_SCALE
            )
            if img:
                self.info_icon = ctk.CTkImage(
                    light_image=img, dark_image=img, size=(24, 24)
                )
        except (FileNotFoundError, OSError, ValueError):
            self.info_icon = None

    def load_delete_icon(self):
        try:
            img = self.load_svg_image(
                os.path.join(self.images_dir, "delete.svg"), self.SVG_RASTER_SCALE
            )
            if img:
                sz = self.calculate_delete_icon_size(self.BASE_KEY_SIZE)
                self.delete_icon = ctk.CTkImage(
                    light_image=img, dark_image=img, size=(sz, sz)
                )
        except (FileNotFoundError, OSError, ValueError):
            self.delete_icon = None

    def load_lightning_icon(self, size=18):
        try:
            img = self.load_svg_image(
                os.path.join(self.images_dir, "lightning.svg"), self.SVG_RASTER_SCALE
            )
            if img:
                self.lightning_icon = ctk.CTkImage(
                    light_image=img, dark_image=img, size=(size, size)
                )
        except (FileNotFoundError, OSError, ValueError):
            self.lightning_icon = None

    def calculate_delete_icon_size(self, key_size):
        return int(
            max(16, min(40, key_size * self.DELETE_ICON_BASE_SIZE / self.BASE_KEY_SIZE))
        )

    def update_delete_icon_size(self, key_size):
        if self.delete_icon:
            sz = self.calculate_delete_icon_size(key_size)
            self.delete_icon.configure(size=(sz, sz))

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
        for r in range(4):
            self.question_container.grid_rowconfigure(r, weight=1 if r == 1 else 0)

        img_sz = self.get_scaled_image_size()
        self.image_frame = ctk.CTkFrame(
            self.question_container, fg_color="transparent", height=img_sz
        )
        self.image_frame.grid(row=0, column=0, sticky="ew", pady=(20, 10))
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

        def_frame = ctk.CTkFrame(self.question_container, fg_color="transparent")
        def_frame.grid(row=1, column=0, sticky="nsew", padx=30, pady=10)
        def_frame.grid_columnconfigure(0, weight=1)
        def_frame.grid_rowconfigure(0, weight=1)

        self.load_info_icon()
        def_inner = ctk.CTkFrame(def_frame, fg_color="transparent")
        def_inner.grid(row=0, column=0, sticky="")
        self.info_icon_label = ctk.CTkLabel(def_inner, text="", image=self.info_icon)
        self.info_icon_label.grid(row=0, column=0, sticky="n", padx=(0, 8), pady=(2, 0))
        self.definition_label = ctk.CTkLabel(
            def_inner,
            text="Loading question...",
            font=self.definition_font,
            text_color=self.COLORS["text_medium"],
            wraplength=600,
            justify="left",
            anchor="w",
        )
        self.definition_label.grid(row=0, column=1, sticky="w")

        box_sz = self.get_scaled_box_size()
        self.answer_boxes_frame = ctk.CTkFrame(
            self.question_container,
            fg_color="transparent",
            width=10 * (box_sz + 6),
            height=box_sz + 4,
        )
        self.answer_boxes_frame.grid(row=2, column=0, pady=(10, 8))
        self.answer_boxes_frame.grid_propagate(False)

        self.feedback_label = ctk.CTkLabel(
            self.question_container,
            text="",
            font=self.feedback_font,
            text_color=self.COLORS["feedback_correct"],
        )
        self.feedback_label.grid(row=3, column=0, pady=(0, 16))

        self.build_wildcards_panel()

    def build_wildcards_panel(self):
        self.wildcards_frame = ctk.CTkFrame(
            self.question_container, fg_color="transparent"
        )
        self.wildcards_frame.grid(
            row=0, column=1, rowspan=4, sticky="ns", padx=(0, 24), pady=24
        )
        self.wildcards_frame.grid_rowconfigure(0, weight=1)
        self.wildcards_frame.grid_rowconfigure(5, weight=1)

        # Size to fit the largest content (snowflake emoji)
        wc_sz, wc_font = 64, 18
        font = ctk.CTkFont(family="Poppins ExtraBold", size=wc_font, weight="bold")
        charges_font = ctk.CTkFont(family="Poppins SemiBold", size=14, weight="bold")

        # Charges display
        self.charges_frame = ctk.CTkFrame(self.wildcards_frame, fg_color="transparent")
        self.charges_frame.grid(row=1, column=0, pady=(0, 12))

        # Load lightning icon
        self.load_lightning_icon()
        if self.lightning_icon:
            self.lightning_icon_label = ctk.CTkLabel(
                self.charges_frame, text="", image=self.lightning_icon
            )
            self.lightning_icon_label.grid(row=0, column=0, padx=(0, 4))

        self.charges_label = ctk.CTkLabel(
            self.charges_frame,
            text=str(self.wildcard_manager.get_charges()),
            font=charges_font,
            text_color=self.COLORS["warning_yellow"],
        )
        self.charges_label.grid(row=0, column=1)

        self.wildcard_x2_btn = ctk.CTkButton(
            self.wildcards_frame,
            text="X2",
            font=font,
            width=wc_sz,
            height=wc_sz,
            corner_radius=wc_sz // 2,
            fg_color="#FFC553",
            hover_color="#E5B04A",
            text_color="white",
            command=self.on_wildcard_x2,
        )
        self.wildcard_x2_btn.grid(row=2, column=0, pady=8)

        self.wildcard_hint_btn = ctk.CTkButton(
            self.wildcards_frame,
            text="A",
            font=font,
            width=wc_sz,
            height=wc_sz,
            corner_radius=wc_sz // 2,
            fg_color="#00CFC5",
            hover_color="#00B5AD",
            text_color="white",
            command=self.on_wildcard_hint,
        )
        self.wildcard_hint_btn.grid(row=3, column=0, pady=8)

        self.wildcard_freeze_btn = ctk.CTkButton(
            self.wildcards_frame,
            text="❄",
            font=font,
            width=wc_sz,
            height=wc_sz,
            corner_radius=wc_sz // 2,
            fg_color="#005DFF",
            hover_color="#0048CC",
            text_color="white",
            command=self.on_wildcard_freeze,
        )
        self.wildcard_freeze_btn.grid(row=4, column=0, pady=8)

        # Initial state update
        self.update_wildcard_buttons_state()

    def on_wildcard_x2(self):
        pass

    def on_wildcard_hint(self):
        pass

    def on_wildcard_freeze(self):
        pass

    def update_charges_display(self):
        """Update the charges label to reflect current charges."""
        if self.charges_label:
            charges = self.wildcard_manager.get_charges()
            self.charges_label.configure(text=str(charges))

    def update_wildcard_buttons_state(self):
        """Update wildcard button states based on available charges and blocking rules."""
        charges = self.wildcard_manager.get_charges()
        double_blocked = self.wildcard_manager.is_double_points_blocked()
        others_blocked = self.wildcard_manager.are_other_wildcards_blocked()

        # X2 Button (costs 2, blocked if other wildcards used first)
        if self.wildcard_x2_btn:
            can_use_x2 = (
                charges >= self.wildcard_manager.COST_DOUBLE_POINTS
                and not double_blocked
            )
            # Update button text based on current multiplier
            mult = self.wildcard_manager.get_points_multiplier()
            btn_text = f"X{mult}" if mult > 1 else "X2"

            if can_use_x2:
                # Check if already active (stacked)
                if self.wildcard_manager.is_double_points_active():
                    self.wildcard_x2_btn.configure(
                        text=btn_text,
                        fg_color="#4CAF50",
                        hover_color="#45A049",
                        state="normal",
                    )
                else:
                    self.wildcard_x2_btn.configure(
                        text=btn_text,
                        fg_color="#FFC553",
                        hover_color="#E5B04A",
                        state="normal",
                    )
            else:
                self.wildcard_x2_btn.configure(
                    text=btn_text,
                    fg_color="#999999",
                    hover_color="#999999",
                    state="disabled",
                )

        # Hint Button (costs 1, blocked if double points used)
        if self.wildcard_hint_btn:
            can_use_hint = (
                charges >= self.wildcard_manager.COST_REVEAL_LETTER
                and not others_blocked
            )
            if can_use_hint:
                self.wildcard_hint_btn.configure(
                    fg_color="#00CFC5",
                    hover_color="#00B5AD",
                    state="normal",
                )
            else:
                self.wildcard_hint_btn.configure(
                    fg_color="#999999",
                    hover_color="#999999",
                    state="disabled",
                )

        # Freeze Button (costs 1, blocked if double points used or already frozen)
        if self.wildcard_freeze_btn:
            can_use_freeze = (
                charges >= self.wildcard_manager.COST_FREEZE_TIMER
                and not others_blocked
                and not self.wildcard_manager.is_timer_frozen()
            )
            if self.wildcard_manager.is_timer_frozen():
                # Already frozen, show active state
                self.wildcard_freeze_btn.configure(
                    fg_color="#4CAF50",
                    hover_color="#4CAF50",
                    state="disabled",
                )
            elif can_use_freeze:
                self.wildcard_freeze_btn.configure(
                    fg_color="#005DFF",
                    hover_color="#0048CC",
                    state="normal",
                )
            else:
                self.wildcard_freeze_btn.configure(
                    fg_color="#999999",
                    hover_color="#999999",
                    state="disabled",
                )

        self.update_charges_display()

    def reset_wildcard_button_colors(self):
        """Reset wildcard buttons for a new question."""
        self.update_wildcard_buttons_state()

    def reset_timer_visuals(self):
        """Reset timer appearance to default (unfrozen state)."""
        self.timer_frozen_visually = False
        if self.timer_label:
            self.timer_label.configure(text_color="white")
        if self.timer_icon_label and self.clock_icon:
            self.timer_icon_label.configure(image=self.clock_icon)

    def apply_freeze_timer_visuals(self):
        """Apply frozen visual state to timer (blue color and freeze icon)."""
        self.timer_frozen_visually = True
        if self.timer_label:
            self.timer_label.configure(text_color="#D0E7FF")
        if self.timer_icon_label and self.freeze_icon:
            self.timer_icon_label.configure(image=self.freeze_icon)

    def build_keyboard(self):
        self.keyboard_frame = ctk.CTkFrame(self.main, fg_color="transparent")
        self.keyboard_frame.grid(row=2, column=0, pady=(0, 16), padx=256, sticky="ew")
        self.keyboard_frame.grid_columnconfigure(0, weight=1)

        self.keyboard_buttons.clear()
        self.key_button_map.clear()
        self.delete_button = None
        self.load_delete_icon()

        for row_idx, row_keys in enumerate(self.KEYBOARD_LAYOUT):
            row_frame = ctk.CTkFrame(self.keyboard_frame, fg_color="transparent")
            row_frame.grid(row=row_idx, column=0, pady=4, sticky="ew")
            row_frame.grid_columnconfigure(0, weight=1)
            row_frame.grid_columnconfigure(2, weight=1)
            inner = ctk.CTkFrame(row_frame, fg_color="transparent")
            inner.grid(row=0, column=1)

            for col, key in enumerate(row_keys):
                is_del = key == "⌫"
                w = int(self.BASE_KEY_SIZE * 1.8) if is_del else self.BASE_KEY_SIZE
                fg = self.COLORS["danger_red"] if is_del else self.COLORS["key_bg"]
                hv = self.COLORS["danger_hover"] if is_del else self.COLORS["key_hover"]
                tc = "white" if is_del else self.COLORS["text_dark"]
                img = self.delete_icon if is_del else None
                txt = "" if img else key

                btn = ctk.CTkButton(
                    inner,
                    text=txt,
                    image=img,
                    font=self.keyboard_font,
                    width=w,
                    height=self.BASE_KEY_SIZE,
                    fg_color=fg,
                    hover_color=hv,
                    text_color=tc,
                    border_width=2,
                    border_color=self.COLORS["header_bg"],
                    corner_radius=8,
                    command=lambda k=key: self.on_key_press(k),
                )
                btn.grid(row=0, column=col, padx=12)
                self.keyboard_buttons.append(btn)
                self.key_button_map[key] = btn
                if is_del:
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
        box_sz = self.get_scaled_box_size()
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

        revealed = self.wildcard_manager.get_revealed_positions()
        for i in range(word_length):
            box = self.answer_box_labels[i]
            has_char = i < len(self.current_answer) and self.current_answer[i].strip()
            if has_char:
                fg = (
                    self.COLORS["success_green"]
                    if i in revealed
                    else self.COLORS["answer_box_filled"]
                )
                box.configure(
                    text=self.current_answer[i],
                    fg_color=fg,
                    width=box_sz,
                    height=box_sz,
                )
            else:
                box.configure(
                    text="",
                    fg_color=self.COLORS["answer_box_empty"],
                    width=box_sz,
                    height=box_sz,
                )
            box.grid(row=0, column=i, padx=3)

        for i in range(word_length, len(self.answer_box_labels)):
            self.answer_box_labels[i].grid_remove()

        self.answer_boxes_frame.configure(
            width=max(box_sz, word_length * (box_sz + 6)), height=box_sz + 4
        )

    def get_current_scale(self):
        w, h = max(self.parent.winfo_width(), 1), max(self.parent.winfo_height(), 1)
        s = min(w / self.BASE_DIMENSIONS[0], h / self.BASE_DIMENSIONS[1])
        return max(self.SCALE_LIMITS[0], min(self.SCALE_LIMITS[1], s))

    def get_scaled_image_size(self, scale=None):
        s = scale or self.get_current_scale()
        return int(
            max(self.IMAGE_MIN_SIZE, min(self.IMAGE_MAX_SIZE, self.BASE_IMAGE_SIZE * s))
        )

    def get_scaled_box_size(self, scale=None):
        s = scale or self.get_current_scale()
        return int(
            max(
                self.ANSWER_BOX_MIN_SIZE,
                min(self.ANSWER_BOX_MAX_SIZE, self.BASE_ANSWER_BOX_SIZE * s),
            )
        )

    def load_svg_image(self, svg_path, scale=1.0):
        try:
            svg_photo = TkSvgImage(file=str(svg_path), scale=scale)
            return ImageTk.getimage(svg_photo).convert("RGBA")
        except (FileNotFoundError, ValueError) as e:
            print(f"Error loading SVG image '{svg_path}': {e}")
            return None

    def on_key_press(self, key):
        pass

    def on_skip(self):
        pass

    def on_check(self):
        pass

    def toggle_audio(self):
        pass

    def return_to_menu(self):
        pass

    def cleanup(self):
        pass

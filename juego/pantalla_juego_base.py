import json
import tkinter as tk

import customtkinter as ctk

from juego.app_paths import (
    get_data_questions_path,
    get_data_root,
    get_resource_audio_dir,
    get_resource_images_dir,
    get_resource_root,
    get_user_images_dir,
)
from juego.comodines import WildcardManager
from juego.image_handler import ImageHandler
from juego.logica import ScoringSystem
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
    KEYBOARD_LAYOUT,
    GameFontRegistry,
    GameSizeCalculator,
)
from juego.responsive_helpers import ResponsiveScaler
from juego.tts_service import TTSService


class GameScreenBase:
    # Import constants from config
    BASE_DIMENSIONS = GAME_BASE_DIMENSIONS
    SCALE_LIMITS = GAME_SCALE_LIMITS
    RESIZE_DELAY = GAME_RESIZE_DELAY
    COLORS = GAME_COLORS
    ICONS = GAME_ICONS
    BASE_SIZES = GAME_BASE_SIZES
    KEYBOARD_LAYOUT = KEYBOARD_LAYOUT

    # SVG rendering scale
    SVG_RASTER_SCALE = 2.0

    def __init__(
        self, parent, on_return_callback=None, tts_service=None, sfx_service=None
    ):
        self.parent = parent
        self.on_return_callback = on_return_callback
        self.sfx = sfx_service

        # Game state
        self.current_question = None
        self.questions = []
        self.available_questions = []
        self.score = 0
        self.current_answer = ""
        self.timer_seconds = 0
        self.audio_enabled = True
        if self.sfx and hasattr(self.sfx, "is_muted"):
            self.audio_enabled = not self.sfx.is_muted()
        self.timer_running = False
        self.timer_job = None
        self.questions_answered = 0
        self.game_completed = False
        self.scoring_system = None
        self.wildcard_manager = WildcardManager()
        self.question_timer = 0
        self.question_mistakes = 0

        # Resize handling
        self.resize_job = None

        # UI component references - Main layout
        self.main = None
        self.header_frame = None
        self.header_left_container = None
        self.header_center_container = None
        self.header_right_container = None

        # Header components
        self.back_button = None
        self.back_arrow_icon = None
        self.timer_container = None
        self.score_container = None
        self.audio_container = None
        self.timer_label = None
        self.timer_icon_label = None
        self.score_label = None
        self.star_icon_label = None
        self.multiplier_label = None
        self.audio_toggle_btn = None

        # Question container components
        self.question_container = None
        self.image_frame = None
        self.image_label = None
        self.definition_frame = None
        self.definition_scroll_wrapper = None
        self.definition_scroll = None
        self.def_inner = None
        self.definition_label = None
        self._definition_scrollbar_visible = None
        self._definition_scrollbar_manager = None
        self._definition_scroll_update_job = None
        self.answer_boxes_frame = None
        self.answer_box_labels = []

        # Keyboard components
        self.keyboard_frame = None
        self.keyboard_buttons = []
        self.delete_button = None
        self.key_button_map = {}

        # Action buttons
        self.action_buttons_frame = None
        self.skip_button = None
        self.check_button = None

        # Image references
        self.current_image = None

        # Icon references
        self.audio_icon_on = None
        self.audio_icon_off = None
        self.clock_icon = None
        self.star_icon = None
        self.delete_icon = None
        self.freeze_icon = None
        self.info_icon = None
        self.info_icon_label = None
        self.lightning_icon = None
        self.lightning_icon_label = None
        self.freeze_wildcard_icon = None

        # Visual state tracking
        self.timer_frozen_visually = False
        self.double_points_visually_active = False

        # Wildcards panel components
        self.wildcards_frame = None
        self.wildcard_x2_btn = None
        self.wildcard_hint_btn = None
        self.wildcard_freeze_btn = None
        self.charges_frame = None
        self.charges_label = None

        # Feedback components
        self.feedback_label = None
        self.feedback_animation_job = None

        # Modal references
        self.completion_modal = None
        self.summary_modal = None
        self.skip_modal = None

        # Game flow state
        self.processing_correct_answer = False
        self.awaiting_modal_decision = False
        self.stored_modal_data = None
        self.question_history = []
        self.viewing_history_index = -1

        # Paths
        resource_images_dir = get_resource_images_dir()
        resource_audio_dir = get_resource_audio_dir()
        data_root = get_data_root()
        resource_root = get_resource_root()

        self.images_dir = resource_images_dir
        self.audio_dir = resource_audio_dir
        self.questions_path = get_data_questions_path()

        # Image handler for icon loading
        self.image_handler = ImageHandler(
            self.images_dir,
            user_images_dir=get_user_images_dir(),
            data_root=data_root,
            resource_root=resource_root,
        )

        # TTS service
        self.tts = tts_service or TTSService(self.audio_dir)

        # Physical keyboard handling
        self.physical_key_pressed = None
        self.key_feedback_job = None

        # Font attributes (set by font_registry.attach_attributes)
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

        # Initialize responsive system
        self.init_responsive_system()

        # Load data and build UI
        self.load_questions()
        self.build_ui()

    def init_responsive_system(self):
        # Create scaler
        self.scaler = ResponsiveScaler(
            self.BASE_DIMENSIONS,
            self.SCALE_LIMITS,
            global_scale_factor=GAME_GLOBAL_SCALE_FACTOR,
        )

        # Create size calculator
        self.size_calc = GameSizeCalculator(self.scaler, GAME_PROFILES)

        # Create font registry and attach fonts as attributes
        self.font_registry = GameFontRegistry(GAME_FONT_SPECS)
        self.font_registry.attach_attributes(self)

        # Store base and min sizes for font scaling
        self.font_base_sizes = self.font_registry.base_sizes
        self.font_min_sizes = self.font_registry.min_sizes

        # State tracking
        self.current_scale = 1.0
        self.current_window_width = self.BASE_DIMENSIONS[0]
        self.current_window_height = self.BASE_DIMENSIONS[1]
        self.size_state = {}

        # Icon cache for efficient resizing
        self.icon_cache = {}

    def _get_window_scaling(self):
        root = self.parent.winfo_toplevel() if self.parent else None
        try:
            scaling = ctk.ScalingTracker.get_window_scaling(root) if root else 1.0
        except (AttributeError, KeyError):
            scaling = 1.0
        if not scaling or scaling <= 0:
            return 1.0
        return scaling

    def _get_logical_dimensions(self):
        if not self.parent or not self.parent.winfo_exists():
            return self.BASE_DIMENSIONS
        scaling = self._get_window_scaling()
        width = max(int(round(self.parent.winfo_width() / scaling)), 1)
        height = max(int(round(self.parent.winfo_height() / scaling)), 1)
        return width, height

    def get_current_scale(self):
        w, h = self._get_logical_dimensions()
        low_res_profile = GAME_PROFILES.get("low_res")
        return self.scaler.calculate_scale(w, h, low_res_profile)

    def scale_value(self, base, scale, min_value=None, max_value=None):
        return self.scaler.scale_value(base, scale, min_value, max_value)

    def get_scaled_image_size(self, scale=None):
        if self.size_state and "image_size" in self.size_state:
            return self.size_state["image_size"]
        s = scale or self.get_current_scale()
        return self.scale_value(
            self.BASE_SIZES["image_base"],
            s,
            self.BASE_SIZES["image_min"],
            self.BASE_SIZES["image_max"],
        )

    def get_scaled_box_size(self, scale=None):
        if self.size_state and "answer_box" in self.size_state:
            return self.size_state["answer_box"]
        s = scale or self.get_current_scale()
        return self.scale_value(
            self.BASE_SIZES["answer_box_base"],
            s,
            self.BASE_SIZES["answer_box_min"],
            self.BASE_SIZES["answer_box_max"],
        )

    def load_questions(self):
        try:
            with open(self.questions_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.questions = data.get("questions", [])
                self.available_questions = list(self.questions)
                self.scoring_system = ScoringSystem(len(self.questions))
                self.wildcard_manager.reset_game()
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading questions: {e}")
            self.questions = []
            self.available_questions = []
            self.scoring_system = ScoringSystem(1)
            self.wildcard_manager.reset_game()

    def build_ui(self):
        # Clear existing widgets
        for widget in self.parent.winfo_children():
            widget.destroy()

        # Configure parent grid
        self.parent.grid_rowconfigure(0, weight=1)
        self.parent.grid_columnconfigure(0, weight=1)

        # Main container
        self.main = ctk.CTkFrame(self.parent, fg_color=self.COLORS["bg_light"])
        self.main.grid(row=0, column=0, sticky="nsew")

        # Main layout: header, question area, keyboard, action buttons
        self.main.grid_rowconfigure(0, weight=0)  # Header
        self.main.grid_rowconfigure(1, weight=1)  # Question container
        self.main.grid_rowconfigure(2, weight=0)  # Keyboard
        self.main.grid_rowconfigure(3, weight=0)  # Action buttons
        self.main.grid_columnconfigure(0, weight=1)

        # Build sections
        self.build_header()
        self.build_question_container()
        self.build_keyboard()
        self.build_action_buttons()

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

        # Spanned layout: timer left, score center, mute right
        self.header_frame.grid_columnconfigure(0, weight=1, uniform="header_side")
        self.header_frame.grid_columnconfigure(1, weight=0)
        self.header_frame.grid_columnconfigure(2, weight=1, uniform="header_side")
        self.header_frame.grid_rowconfigure(0, weight=1)

        # Load header icons
        self.load_header_icons()

        # Left container (timer)
        self.header_left_container = ctk.CTkFrame(
            self.header_frame, fg_color="transparent"
        )
        self.header_left_container.grid(
            row=0, column=0, sticky="w", padx=(self.BASE_SIZES["header_pad_x"], 0)
        )

        # Center container (score)
        self.header_center_container = ctk.CTkFrame(
            self.header_frame, fg_color="transparent"
        )
        self.header_center_container.grid(row=0, column=1)

        # Right container (audio toggle)
        self.header_right_container = ctk.CTkFrame(
            self.header_frame, fg_color="transparent"
        )
        self.header_right_container.grid(
            row=0, column=2, sticky="e", padx=(0, self.BASE_SIZES["header_pad_x"])
        )

        # Build timer section
        self.build_timer_section()

        # Build score section
        self.build_score_section()

        # Build audio toggle
        self.build_audio_section()

    def build_timer_section(self):
        self.timer_container = ctk.CTkFrame(
            self.header_left_container, fg_color="transparent"
        )
        self.timer_container.grid(row=0, column=0)

        self.timer_icon_label = ctk.CTkLabel(
            self.timer_container, text="", image=self.clock_icon
        )
        self.timer_icon_label.grid(row=0, column=0, padx=(0, 8))

        self.timer_label = ctk.CTkLabel(
            self.timer_container,
            text="00:00",
            font=self.timer_font,
            text_color="white",
        )
        self.timer_label.grid(row=0, column=1)

    def build_score_section(self):
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
            self.score_container,
            text="0",
            font=self.score_font,
            text_color="white",
        )
        self.score_label.grid(row=0, column=1)

        # Multiplier label (hidden by default)
        self.multiplier_label = ctk.CTkLabel(
            self.score_container,
            text="",
            font=self.multiplier_font,
            text_color=self.COLORS["warning_yellow"],
            width=star_sz + 8,
        )
        self.multiplier_label.grid(row=0, column=2, padx=(8, 0))
        self.multiplier_label.grid_remove()

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
            pady=self.BASE_SIZES["container_pad_y"],
        )

        # Grid configuration for question container
        # All rows have weight=0 so they take natural heights based on content
        # This prevents the definition row from being squeezed out at low resolutions
        self.question_container.grid_columnconfigure(0, weight=1)
        self.question_container.grid_columnconfigure(1, weight=0)
        for r in range(4):
            self.question_container.grid_rowconfigure(r, weight=0)

        # Build sections
        self.build_image_section()
        self.build_definition_section()
        self.build_answer_boxes_section()
        self.build_feedback_section()
        self.build_wildcards_panel()

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
        # Store reference to frame for responsive updates
        self.definition_frame = ctk.CTkFrame(
            self.question_container, fg_color="transparent"
        )
        self.definition_frame.grid(row=1, column=0, sticky="ew", padx=24, pady=2)
        self.definition_frame.grid_columnconfigure(0, weight=1)

        self.load_info_icon()

        # Wrapper with fixed height to constrain scrollable frame
        self.definition_scroll_wrapper = ctk.CTkFrame(
            self.definition_frame,
            fg_color="transparent",
            height=45,
        )
        self.definition_scroll_wrapper.grid(row=0, column=0, sticky="ew")
        self.definition_scroll_wrapper.grid_propagate(False)  # Force fixed height
        self.definition_scroll_wrapper.grid_rowconfigure(0, weight=1)
        self.definition_scroll_wrapper.grid_columnconfigure(0, weight=1)

        # Scrollable frame inside wrapper
        self.definition_scroll = ctk.CTkScrollableFrame(
            self.definition_scroll_wrapper,
            fg_color="transparent",
            scrollbar_button_color="#9B9B9B",
            scrollbar_button_hover_color="#666666",
        )
        self.definition_scroll.grid(row=0, column=0, sticky="nsew")
        self.definition_scroll.grid_columnconfigure(0, weight=1)

        # Inner frame that centers content but expands horizontally
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
            text="Loading question...",
            font=self.definition_font,
            text_color=self.COLORS["text_medium"],
            wraplength=self.BASE_SIZES["definition_wrap_base"],
            justify="left",
            anchor="w",
        )
        self.definition_label.grid(row=0, column=1, sticky="nw")

    def set_definition_text(self, text):
        if self.definition_label and self.definition_label.winfo_exists():
            self.definition_label.configure(text=text)
        self.queue_definition_scroll_update()

    def queue_definition_scroll_update(self):
        if not self.parent or not self.parent.winfo_exists():
            return
        if self._definition_scroll_update_job:
            try:
                self.parent.after_cancel(self._definition_scroll_update_job)
            except tk.TclError:
                pass
            self._definition_scroll_update_job = None
        try:
            self._definition_scroll_update_job = self.parent.after_idle(
                self.update_definition_scrollbar_visibility
            )
        except tk.TclError:
            self._definition_scroll_update_job = None
            self.update_definition_scrollbar_visibility()

    def update_definition_scrollbar_visibility(self):
        self._definition_scroll_update_job = None
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

        needs_scroll = content_height > (wrapper_height + 2)
        self._set_definition_scrollbar_visible(needs_scroll)

    def _set_definition_scrollbar_visible(self, visible):
        if self._definition_scrollbar_visible is visible:
            return

        scrollbar = self._get_scrollbar_widget(self.definition_scroll)
        if not scrollbar or not scrollbar.winfo_exists():
            return

        manager = self._definition_scrollbar_manager or scrollbar.winfo_manager()
        if not manager:
            manager = "grid"
        self._definition_scrollbar_manager = manager

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

        self._definition_scrollbar_visible = visible

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

    def build_answer_boxes_section(self):
        box_sz = self.get_scaled_box_size()

        self.answer_boxes_frame = ctk.CTkFrame(
            self.question_container,
            fg_color="transparent",
            width=10 * (box_sz + 8),
            height=box_sz + 16,  # Extra padding to prevent clipping at low res
        )
        self.answer_boxes_frame.grid(row=2, column=0, pady=(6, 6), padx=20)
        # Configure internal grid to center content without stretching a single column.
        self.answer_boxes_frame.grid_rowconfigure(0, weight=1)
        self.answer_boxes_frame.grid_anchor("center")

    def build_feedback_section(self):
        self.feedback_label = ctk.CTkLabel(
            self.question_container,
            text="",
            font=self.feedback_font,
            text_color=self.COLORS["feedback_correct"],
        )
        self.feedback_label.grid(row=3, column=0, pady=(0, 4), padx=20)

    def build_wildcards_panel(self):
        self.wildcards_frame = ctk.CTkFrame(
            self.question_container, fg_color="transparent"
        )
        # Use sticky="n" to anchor at top, natural content height
        self.wildcards_frame.grid(
            row=0, column=1, rowspan=4, sticky="n", padx=(0, 16), pady=12
        )

        wc_sz = self.BASE_SIZES["wildcard_size"]
        wc_font = self.BASE_SIZES["wildcard_font_size"]
        font = ctk.CTkFont(family="Poppins ExtraBold", size=wc_font, weight="bold")
        charges_font = ctk.CTkFont(family="Poppins SemiBold", size=14, weight="bold")

        # Calculate button width to accommodate text like "X16" (stacked multipliers)
        # Use 1.5x the height for a nice pill shape that fits all text
        wc_btn_width = int(wc_sz * 1.5)
        wc_corner = wc_sz // 2  # Keep corner radius based on height for pill shape

        # Charges display
        self.charges_frame = ctk.CTkFrame(self.wildcards_frame, fg_color="transparent")
        self.charges_frame.grid(row=1, column=0, pady=(0, 6))

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

        # X2 button - use consistent width for all buttons
        self.wildcard_x2_btn = ctk.CTkButton(
            self.wildcards_frame,
            text="X2",
            font=font,
            width=wc_btn_width,
            height=wc_sz,
            corner_radius=wc_corner,
            fg_color=self.COLORS["wildcard_x2"],
            hover_color=self.COLORS["wildcard_x2_hover"],
            text_color="white",
            command=self.on_wildcard_x2,
        )
        self.wildcard_x2_btn.grid(row=2, column=0, pady=4)

        # Hint button - same width as X2 for consistency
        self.wildcard_hint_btn = ctk.CTkButton(
            self.wildcards_frame,
            text="A",
            font=font,
            width=wc_btn_width,
            height=wc_sz,
            corner_radius=wc_corner,
            fg_color=self.COLORS["wildcard_hint"],
            hover_color=self.COLORS["wildcard_hint_hover"],
            text_color="white",
            command=self.on_wildcard_hint,
        )
        self.wildcard_hint_btn.grid(row=3, column=0, pady=4)

        # Freeze button - same width as others for consistency
        self.load_freeze_wildcard_icon(int(wc_sz * 0.5))

        self.wildcard_freeze_btn = ctk.CTkButton(
            self.wildcards_frame,
            text="" if self.freeze_wildcard_icon else "❄",
            image=self.freeze_wildcard_icon,
            font=font,
            width=wc_btn_width,
            height=wc_sz,
            corner_radius=wc_corner,
            fg_color=self.COLORS["wildcard_freeze"],
            hover_color=self.COLORS["wildcard_freeze_hover"],
            text_color="white",
            command=self.on_wildcard_freeze,
        )
        self.wildcard_freeze_btn.grid(row=4, column=0, pady=4)

        self.update_wildcard_buttons_state()

    def build_keyboard(self):
        self.keyboard_frame = ctk.CTkFrame(self.main, fg_color="transparent")
        self.keyboard_frame.grid(
            row=2,
            column=0,
            pady=(0, 16),
            padx=self.BASE_SIZES["keyboard_pad_x"],
            sticky="ew",
        )
        self.keyboard_frame.grid_columnconfigure(0, weight=1)

        self.keyboard_buttons.clear()
        self.key_button_map.clear()
        self.delete_button = None
        self.load_delete_icon()

        key_sz = self.BASE_SIZES["key_base"]
        key_gap = self.BASE_SIZES["key_gap"]
        key_width_ratio = self.BASE_SIZES.get("key_width_ratio", 1.0)
        delete_ratio = self.BASE_SIZES.get("delete_key_width_ratio", 1.8)

        for row_idx, row_keys in enumerate(self.KEYBOARD_LAYOUT):
            row_frame = ctk.CTkFrame(self.keyboard_frame, fg_color="transparent")
            row_frame.grid(row=row_idx, column=0, pady=4, sticky="ew")
            row_frame.grid_columnconfigure(0, weight=1)
            row_frame.grid_columnconfigure(2, weight=1)

            inner = ctk.CTkFrame(row_frame, fg_color="transparent")
            inner.grid(row=0, column=1)

            for col, key in enumerate(row_keys):
                is_del = key == "⌫"
                w = (
                    int(key_sz * delete_ratio * key_width_ratio)
                    if is_del
                    else int(key_sz * key_width_ratio)
                )
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
                    height=key_sz,
                    fg_color=fg,
                    hover_color=hv,
                    text_color=tc,
                    border_width=2,
                    border_color=self.COLORS["header_bg"],
                    corner_radius=8,
                    command=lambda k=key: self.on_key_press(k),
                )
                btn.grid(row=0, column=col, padx=key_gap // 2)
                self.keyboard_buttons.append(btn)
                self.key_button_map[key] = btn
                if is_del:
                    self.delete_button = btn

    def build_action_buttons(self):
        self.action_buttons_frame = ctk.CTkFrame(self.main, fg_color="transparent")
        self.action_buttons_frame.grid(row=3, column=0, pady=(0, 24))

        btn_width = self.BASE_SIZES["action_button_width"]
        btn_height = self.BASE_SIZES["action_button_height"]
        btn_gap = self.BASE_SIZES["action_button_gap"]
        corner_r = self.BASE_SIZES["action_corner_radius"]

        self.skip_button = ctk.CTkButton(
            self.action_buttons_frame,
            text="Skip",
            font=self.button_font,
            width=btn_width,
            height=btn_height,
            fg_color=self.COLORS["bg_light"],
            hover_color=self.COLORS["border_medium"],
            text_color="black",
            border_width=2,
            border_color="black",
            corner_radius=corner_r,
            command=self.on_skip,
        )
        self.skip_button.grid(row=0, column=0, padx=btn_gap // 2)

        self.check_button = ctk.CTkButton(
            self.action_buttons_frame,
            text="Check",
            font=self.button_font,
            width=btn_width,
            height=btn_height,
            fg_color=self.COLORS["primary_blue"],
            hover_color=self.COLORS["primary_hover"],
            text_color="white",
            corner_radius=corner_r,
            command=self.on_check,
        )
        self.check_button.grid(row=0, column=1, padx=btn_gap // 2)

    def _load_icon(self, icon_key, size):
        return self.image_handler.create_ctk_icon(self.ICONS[icon_key], (size, size))

    def load_header_icons(self):
        self.clock_icon = self._load_icon("clock", 24)
        self.star_icon = self._load_icon("star", 24)
        self.freeze_icon = self._load_icon("freeze", 24)

    def load_audio_icons(self):
        sz = self.BASE_SIZES["audio_icon_base"]
        self.audio_icon_on = self._load_icon("volume_on", sz)
        self.audio_icon_off = self._load_icon("volume_off", sz)

    def load_info_icon(self):
        self.info_icon = self._load_icon("info", 24)

    def load_delete_icon(self):
        self.delete_icon = self._load_icon(
            "delete", self.BASE_SIZES["delete_icon_base"]
        )

    def load_lightning_icon(self, size=18):
        self.lightning_icon = self._load_icon("lightning", size)

    def load_freeze_wildcard_icon(self, size=28):
        self.freeze_wildcard_icon = self._load_icon("freeze", size)

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

    def create_answer_boxes(self, word_length):
        box_sz = self.get_scaled_box_size()
        gap = self.size_state.get("answer_box_gap", 3)
        scale = self.size_state.get("scale", 1.0) if self.size_state else 1.0
        is_compact = self.size_state.get("is_height_constrained", False)
        extra_pad = self.scale_value(16, scale, 8, 20)

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

        revealed = self.wildcard_manager.get_revealed_positions()

        # Configure visible boxes
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
            box.grid(row=0, column=i, padx=gap, pady=4)

        # Hide extra boxes
        for i in range(word_length, len(self.answer_box_labels)):
            self.answer_box_labels[i].grid_remove()

        # Update frame size (extra height padding to prevent clipping at low res)
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

    def on_wildcard_x2(self):
        pass  # Override in logic class

    def on_wildcard_hint(self):
        pass  # Override in logic class

    def on_wildcard_freeze(self):
        pass  # Override in logic class

    def update_charges_display(self):
        if self.charges_label:
            charges = self.wildcard_manager.get_charges()
            self.charges_label.configure(text=str(charges))

    def update_wildcard_buttons_state(self):
        charges = self.wildcard_manager.get_charges()
        double_blocked = self.wildcard_manager.is_double_points_blocked()
        others_blocked = self.wildcard_manager.are_other_wildcards_blocked()

        # X2 Button
        if self.wildcard_x2_btn:
            can_use_x2 = (
                charges >= self.wildcard_manager.COST_DOUBLE_POINTS
                and not double_blocked
            )
            mult = self.wildcard_manager.get_points_multiplier()
            btn_text = f"X{mult}" if mult > 1 else "X2"

            if can_use_x2:
                if self.wildcard_manager.is_double_points_active():
                    self.wildcard_x2_btn.configure(
                        text=btn_text,
                        fg_color=self.COLORS["wildcard_x2"],
                        hover_color=self.COLORS["wildcard_x2_hover"],
                        state="normal",
                    )
                else:
                    self.wildcard_x2_btn.configure(
                        text=btn_text,
                        fg_color=self.COLORS["wildcard_x2"],
                        hover_color=self.COLORS["wildcard_x2_hover"],
                        state="normal",
                    )
            else:
                self.wildcard_x2_btn.configure(
                    text=btn_text,
                    fg_color=self.COLORS["wildcard_disabled"],
                    hover_color=self.COLORS["wildcard_disabled"],
                    state="disabled",
                )

        # Hint Button
        if self.wildcard_hint_btn:
            can_use_hint = (
                charges >= self.wildcard_manager.COST_REVEAL_LETTER
                and not others_blocked
            )
            if can_use_hint:
                self.wildcard_hint_btn.configure(
                    fg_color=self.COLORS["wildcard_hint"],
                    hover_color=self.COLORS["wildcard_hint_hover"],
                    state="normal",
                )
            else:
                self.wildcard_hint_btn.configure(
                    fg_color=self.COLORS["wildcard_disabled"],
                    hover_color=self.COLORS["wildcard_disabled"],
                    state="disabled",
                )

        # Freeze Button
        if self.wildcard_freeze_btn:
            can_use_freeze = (
                charges >= self.wildcard_manager.COST_FREEZE_TIMER
                and not others_blocked
                and not self.wildcard_manager.is_timer_frozen()
            )
            if self.wildcard_manager.is_timer_frozen():
                self.wildcard_freeze_btn.configure(
                    fg_color=self.COLORS["wildcard_x2_active"],
                    hover_color=self.COLORS["wildcard_x2_active"],
                    state="disabled",
                )
            elif can_use_freeze:
                self.wildcard_freeze_btn.configure(
                    fg_color=self.COLORS["wildcard_freeze"],
                    hover_color=self.COLORS["wildcard_freeze_hover"],
                    state="normal",
                )
            else:
                self.wildcard_freeze_btn.configure(
                    fg_color=self.COLORS["wildcard_disabled"],
                    hover_color=self.COLORS["wildcard_disabled"],
                    state="disabled",
                )

        self.update_charges_display()

    def reset_wildcard_button_colors(self):
        self.update_wildcard_buttons_state()

    def reset_timer_visuals(self):
        self.timer_frozen_visually = False
        if self.timer_label:
            self.timer_label.configure(text_color="white")
        if self.timer_icon_label and self.clock_icon:
            self.timer_icon_label.configure(image=self.clock_icon)

    def apply_freeze_timer_visuals(self):
        self.timer_frozen_visually = True
        if self.timer_label:
            self.timer_label.configure(text_color="#D0E7FF")
        if self.timer_icon_label and self.freeze_icon:
            self.timer_icon_label.configure(image=self.freeze_icon)

    def apply_double_points_visuals(self, multiplier=2):
        self.double_points_visually_active = True
        if self.score_label:
            self.score_label.configure(text_color=self.COLORS["warning_yellow"])
        if self.multiplier_label:
            self.multiplier_label.configure(text=f"X{multiplier}")
            self.multiplier_label.grid()

    def reset_double_points_visuals(self):
        self.double_points_visually_active = False
        if self.score_label:
            self.score_label.configure(text_color="white")
        if self.multiplier_label:
            self.multiplier_label.grid_remove()

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

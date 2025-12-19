import customtkinter as ctk

GAME_BASE_DIMENSIONS = (1280, 720)
GAME_SCALE_LIMITS = (0.50, 2.20)  # Support 720p to 4K
GAME_RESIZE_DELAY = 80
GAME_GLOBAL_SCALE_FACTOR = 1.0


GAME_COLORS = {
    # Primary colors
    "primary_blue": "#005DFF",
    "primary_hover": "#003BB8",
    # Status colors
    "success_green": "#00CFC5",
    "success_hover": "#009B94",
    "warning_yellow": "#FFC553",
    "warning_hover": "#CC9A42",
    "danger_red": "#FF4F60",
    "danger_hover": "#CC3F4D",
    # Text colors
    "text_dark": "#202632",
    "text_medium": "#3A3F4B",
    "text_light": "#7A7A7A",
    "text_white": "#FFFFFF",
    # Background colors
    "bg_light": "#F5F7FA",
    "bg_card": "#FFFFFF",
    "bg_modal": "#202632",
    # Border colors
    "border_light": "#E2E7F3",
    "border_medium": "#D3DBEA",
    # Header colors
    "header_bg": "#202632",
    "header_hover": "#273246",
    # Keyboard colors
    "key_bg": "#E8ECF2",
    "key_hover": "#D0D6E0",
    "key_pressed": "#B8C0D0",
    # Answer box colors
    "answer_box_empty": "#E2E7F3",
    "answer_box_filled": "#D0D6E0",
    # Feedback colors
    "feedback_correct": "#00CFC5",
    "feedback_incorrect": "#FF4F60",
    # Wildcard colors
    "wildcard_x2": "#FFC553",
    "wildcard_x2_hover": "#E5B04A",
    "wildcard_x2_active": "#4CAF50",
    "wildcard_hint": "#00CFC5",
    "wildcard_hint_hover": "#00B5AD",
    "wildcard_freeze": "#005DFF",
    "wildcard_freeze_hover": "#0048CC",
    "wildcard_disabled": "#999999",
    # Modal colors
    "modal_border": "#1D6CFF",
    "modal_cancel_bg": "#D0D6E0",
    "modal_cancel_hover": "#B8C0D0",
    "modal_skip_bg": "#FF4F60",
    "modal_skip_hover": "#CC3F4D",
    # Level badge colors
    "level_beginner": "#FF4F60",
    "level_student": "#005DFF",
    "level_professional": "#00CFC5",
    "level_expert": "#CC9A42",
    "level_master": "#7C3AED",
}


GAME_ICONS = {
    "clock": "Clock.svg",
    "star": "star.svg",
    "freeze": "Freeze.svg",
    "lightning": "lightning.svg",
    "delete": "delete.svg",
    "volume_on": "volume-white.svg",
    "volume_off": "volume-mute.svg",
    "arrow": "arrow.svg",
    "info": "info.svg",
}


GAME_BASE_SIZES = {
    # Header
    "header_height": 72,
    "header_pad_x": 24,
    "header_pad_y": 14,
    # Timer and score
    "timer_icon_size": 16,
    "star_icon_size": 16,
    # Audio toggle
    "audio_icon_base": 20,
    "audio_icon_min": 16,
    "audio_icon_max": 32,
    "audio_button_width": 30,
    "audio_button_height": 30,
    # Question container
    "container_pad_x": 20,
    "container_pad_y": 8,
    "container_corner_radius": 14,
    # Image
    "image_base": 120,
    "image_min": 75,
    "image_max": 220,
    # Definition
    "definition_wrap_base": 600,
    "definition_wrap_min": 320,
    "definition_wrap_max": 1000,
    "info_icon_size": 24,
    # Answer boxes
    "answer_box_base": 40,
    "answer_box_min": 28,
    "answer_box_max": 64,
    "answer_box_gap": 3,
    # Keyboard
    "key_base": 40,
    "key_min": 30,
    "key_max": 68,
    "key_gap": 10,
    "key_row_gap": 3,
    "keyboard_pad_x": 256,
    "keyboard_pad_y": 10,
    "delete_icon_base": 26,
    # Action buttons
    "action_button_width": 130,
    "action_button_height": 38,
    "action_button_gap": 14,
    "action_corner_radius": 10,
    # Wildcards
    "wildcard_size": 42,
    "wildcard_min": 32,
    "wildcard_max": 64,
    "wildcard_corner_radius": 21,
    "wildcard_gap": 4,
    "wildcard_font_size": 14,
    "charges_font_size": 12,
    "lightning_icon_size": 14,
    "freeze_icon_ratio": 0.5,
    # Feedback
    "feedback_pad_bottom": 16,
}


GAME_FONT_SPECS = {
    # (family, base_size, weight, min_size)
    "timer": ("Poppins SemiBold", 24, "bold", 14),
    "score": ("Poppins ExtraBold", 28, "bold", 16),
    "definition": ("Open Sans Regular", 15, None, 13),
    "keyboard": ("Poppins SemiBold", 18, "bold", 12),
    "answer_box": ("Poppins ExtraBold", 20, "bold", 14),
    "button": ("Poppins SemiBold", 20, None, 12),
    "header_button": ("Poppins SemiBold", 20, "bold", 12),
    "header_label": ("Poppins SemiBold", 14, None, 10),
    "feedback": ("Poppins SemiBold", 14, "bold", 11),
    "wildcard": ("Poppins ExtraBold", 18, "bold", 12),
    "charges": ("Poppins SemiBold", 14, "bold", 10),
    "multiplier": ("Poppins ExtraBold", 20, "bold", 12),
}


# Header height profile (reduced slightly at lower resolutions to fit content)
GAME_HEADER_HEIGHT_PROFILE = [
    (720, 56),
    (900, 62),
    (1080, 70),
    (1280, 80),
    (1600, 96),
    (1920, 110),
    (2560, 130),
    (3200, 150),
    (3840, 170),
]

# Image size profile (aggressively reduced at low res)
GAME_IMAGE_SIZE_PROFILE = [
    (720, 100),
    (900, 110),
    (1080, 120),
    (1280, 130),
    (1600, 160),
    (1920, 190),
    (2560, 230),
    (3200, 270),
    (3840, 300),
]

# Answer box size profile (slightly reduced at low res)
GAME_ANSWER_BOX_PROFILE = [
    (720, 28),
    (900, 32),
    (1080, 38),
    (1280, 42),
    (1600, 50),
    (1920, 56),
    (2560, 64),
    (3200, 72),
    (3840, 80),
]

# Keyboard key size profile (aggressively reduced at low res)
GAME_KEY_SIZE_PROFILE = [
    (720, 24),
    (900, 28),
    (1080, 36),
    (1280, 46),
    (1600, 54),
    (1920, 62),
    (2560, 72),
    (3200, 82),
    (3840, 90),
]

# Keyboard horizontal padding profile
GAME_KEYBOARD_PAD_PROFILE = [
    (720, 80),
    (900, 140),
    (1080, 200),
    (1280, 256),
    (1600, 340),
    (1920, 420),
    (2560, 560),
    (3200, 700),
    (3840, 800),
]

# Definition wrap length profile - capped to ensure text wraps nicely
# Larger wraplength at high res causes single-line text that clips
GAME_DEFINITION_WRAP_PROFILE = [
    (720, 320),
    (900, 400),
    (1080, 480),
    (1280, 560),
    (1600, 700),
    (1920, 840),
    (2560, 1120),
    (3200, 1400),
    (3840, 1680),
]

# Action button width profile (reduced at low res for more content space)
GAME_ACTION_BUTTON_PROFILE = [
    (720, 100),
    (900, 115),
    (1080, 130),
    (1280, 140),
    (1600, 165),
    (1920, 190),
    (2560, 230),
    (3200, 270),
    (3840, 300),
]

# Wildcard size profile (reduced at low res)
GAME_WILDCARD_SIZE_PROFILE = [
    (720, 32),
    (900, 36),
    (1080, 42),
    (1280, 48),
    (1600, 56),
    (1920, 64),
    (2560, 76),
    (3200, 88),
    (3840, 96),
]

# Container padding profile
GAME_CONTAINER_PAD_PROFILE = [
    (720, 12),
    (900, 16),
    (1080, 20),
    (1280, 24),
    (1600, 32),
    (1920, 40),
    (2560, 52),
    (3200, 64),
    (3840, 76),
]

# Low resolution scale penalty profile
# Only penalize resolutions BELOW the base 720p height
GAME_LOW_RES_SCALE_PROFILE = [
    (480, 0.70),
    (540, 0.80),
    (600, 0.90),
    (720, 1.00),
]


MODAL_BASE_SIZES = {
    # Skip confirmation modal
    "skip_width": 400,
    "skip_height": 200,
    "skip_width_ratio": 0.35,
    "skip_height_ratio": 0.35,
    # Question summary modal
    "summary_width": 450,
    "summary_height": 380,
    "summary_width_ratio": 0.35,
    "summary_height_ratio": 0.48,
    # Game completion modal
    "completion_width": 560,
    "completion_height": 520,
    "completion_width_ratio": 0.42,
    "completion_height_ratio": 0.52,
    # Common
    "header_height": 72,
    "header_min": 48,
    "button_width": 150,
    "button_height": 44,
    "button_corner_radius": 12,
    "corner_radius": 16,
    "border_width": 3,
    "padding": 24,
    "row_padding": 10,
}

MODAL_FONT_SPECS = {
    "title": ("Poppins ExtraBold", 28, "bold", 16),
    "message": ("Poppins SemiBold", 16, "bold", 12),
    "score": ("Poppins ExtraBold", 54, "bold", 28),
    "label": ("Poppins SemiBold", 15, "bold", 11),
    "value": ("Poppins SemiBold", 15, "bold", 11),
    "badge": ("Poppins SemiBold", 14, "bold", 10),
    "footnote": ("Open Sans Regular", 13, None, 10),
    "button": ("Poppins SemiBold", 17, "bold", 12),
    "body": ("Poppins SemiBold", 16, "bold", 12),
}

MODAL_ANIMATION = {
    "delay_ms": 160,
    "fade_steps": 12,
    "fade_step_ms": 30,
}


KEYBOARD_LAYOUT = [
    ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
    ["A", "S", "D", "F", "G", "H", "J", "K", "L"],
    ["Z", "X", "C", "V", "B", "N", "M", "⌫"],
]


LEVEL_BADGE_COLORS = {
    "Beginner": GAME_COLORS["level_beginner"],
    "Student": GAME_COLORS["level_student"],
    "Professional": GAME_COLORS["level_professional"],
    "Expert": GAME_COLORS["level_expert"],
    "Master": GAME_COLORS["level_master"],
}


class GameFontRegistry:

    def __init__(self, specs):
        self._fonts = {}
        self.base_sizes = {}
        self.min_sizes = {}

        for name, (family, size, weight, min_size) in specs.items():
            font = (
                ctk.CTkFont(family=family, size=size, weight=weight)
                if weight
                else ctk.CTkFont(family=family, size=size)
            )
            self._fonts[name] = font
            self.base_sizes[name] = size
            self.min_sizes[name] = min_size or 10

    def get(self, name):
        return self._fonts.get(name)

    def items(self):
        return self._fonts.items()

    def update_scale(self, scale, scaler):
        for name, font in self._fonts.items():
            base_size = self.base_sizes.get(name, 14)
            min_size = self.min_sizes.get(name, 10)
            max_size = base_size * 2.5
            new_size = scaler.scale_value(base_size, scale, min_size, max_size)
            font.configure(size=new_size)

    def attach_attributes(self, target):
        for name, font in self._fonts.items():
            setattr(target, f"{name}_font", font)


class GameSizeCalculator:

    # Height threshold below which we apply compact sizing
    # Set low to disable the aggressive compact mode - use profile scaling instead
    HEIGHT_CONSTRAINED_THRESHOLD = 700

    def __init__(self, scaler, profiles):
        self.scaler = scaler
        self.profiles = profiles

    def calculate_sizes(self, scale, window_width, window_height):
        s = self.scaler.scale_value
        ip = self.scaler.interpolate_profile

        sizes = {}

        # Determine if we're height-constrained (720p or similar low-height displays)
        # Only apply compact sizing when height is actually limited
        is_height_constrained = window_height <= self.HEIGHT_CONSTRAINED_THRESHOLD

        # For height-constrained screens, use the smaller dimension (height) for
        # profile lookups of elements that need to fit vertically
        # This ensures proper sizing at 720p (1280x720) where height is the constraint
        vertical_dimension = (
            min(window_width, window_height) if is_height_constrained else window_width
        )

        # Header - use height for lookup when height-constrained to scale naturally
        # This gives gradual reduction instead of a sudden jump
        header_lookup_dim = (
            min(window_width, window_height) if is_height_constrained else window_width
        )
        sizes["header_height"] = ip(header_lookup_dim, self.profiles["header_height"])
        sizes["header_pad_x"] = s(GAME_BASE_SIZES["header_pad_x"], scale, 16, 72)
        sizes["header_pad_y"] = s(GAME_BASE_SIZES["header_pad_y"], scale, 12, 48)

        # Timer and score icons
        sizes["timer_icon"] = s(GAME_BASE_SIZES["timer_icon_size"], scale, 16, 40)
        sizes["star_icon"] = s(GAME_BASE_SIZES["star_icon_size"], scale, 16, 40)

        # Audio button
        sizes["audio_icon"] = s(
            GAME_BASE_SIZES["audio_icon_base"],
            scale,
            GAME_BASE_SIZES["audio_icon_min"],
            GAME_BASE_SIZES["audio_icon_max"],
        )
        sizes["audio_button_width"] = s(
            GAME_BASE_SIZES["audio_button_width"], scale, 36, 80
        )
        sizes["audio_button_height"] = s(
            GAME_BASE_SIZES["audio_button_height"], scale, 30, 70
        )

        # Question container
        sizes["container_pad_x"] = ip(window_width, self.profiles["container_pad"])
        sizes["container_pad_y"] = s(GAME_BASE_SIZES["container_pad_y"], scale, 8, 50)
        sizes["container_corner_radius"] = s(
            GAME_BASE_SIZES["container_corner_radius"], scale, 12, 36
        )

        # Image - use vertical_dimension for height-constrained, width otherwise
        sizes["image_size"] = ip(vertical_dimension, self.profiles["image_size"])

        # Definition - always use width for wraplength (horizontal constraint)
        sizes["definition_wrap"] = ip(window_width, self.profiles["definition_wrap"])
        sizes["info_icon"] = s(GAME_BASE_SIZES["info_icon_size"], scale, 16, 40)

        # Answer boxes - use vertical_dimension for height-constrained
        sizes["answer_box"] = ip(vertical_dimension, self.profiles["answer_box"])
        sizes["answer_box_gap"] = s(GAME_BASE_SIZES["answer_box_gap"], scale, 2, 6)

        # Keyboard - key sizes use vertical_dimension, padding uses width
        sizes["key_size"] = ip(vertical_dimension, self.profiles["key_size"])
        sizes["key_gap"] = s(GAME_BASE_SIZES["key_gap"], scale, 4, 24)
        sizes["key_row_gap"] = s(GAME_BASE_SIZES["key_row_gap"], scale, 2, 8)
        sizes["keyboard_pad"] = ip(window_width, self.profiles["keyboard_pad"])
        sizes["keyboard_pad_y"] = s(GAME_BASE_SIZES["keyboard_pad_y"], scale, 8, 32)
        sizes["delete_key_width_ratio"] = 1.8
        sizes["delete_icon"] = s(GAME_BASE_SIZES["delete_icon_base"], scale, 16, 48)

        # Action buttons - use vertical_dimension for height-constrained
        sizes["action_button_width"] = ip(
            vertical_dimension, self.profiles["action_button"]
        )
        sizes["action_button_height"] = s(
            GAME_BASE_SIZES["action_button_height"], scale, 32, 80
        )
        sizes["action_button_gap"] = s(
            GAME_BASE_SIZES["action_button_gap"], scale, 8, 32
        )
        sizes["action_corner_radius"] = s(
            GAME_BASE_SIZES["action_corner_radius"], scale, 8, 24
        )

        # Wildcards - use vertical_dimension for height-constrained
        sizes["wildcard_size"] = ip(vertical_dimension, self.profiles["wildcard_size"])
        sizes["wildcard_corner_radius"] = sizes["wildcard_size"] // 2
        sizes["wildcard_gap"] = s(GAME_BASE_SIZES["wildcard_gap"], scale, 4, 16)
        sizes["wildcard_font"] = s(GAME_BASE_SIZES["wildcard_font_size"], scale, 12, 32)
        sizes["charges_font"] = s(GAME_BASE_SIZES["charges_font_size"], scale, 10, 24)
        sizes["lightning_icon"] = s(
            GAME_BASE_SIZES["lightning_icon_size"], scale, 12, 32
        )
        sizes["freeze_icon"] = int(
            sizes["wildcard_size"] * GAME_BASE_SIZES["freeze_icon_ratio"]
        )

        # Feedback
        sizes["feedback_pad_bottom"] = s(
            GAME_BASE_SIZES["feedback_pad_bottom"], scale, 8, 48
        )

        # Store scale and dimensions
        sizes["scale"] = scale
        sizes["window_width"] = window_width
        sizes["window_height"] = window_height
        sizes["is_height_constrained"] = is_height_constrained

        return sizes


GAME_PROFILES = {
    "header_height": GAME_HEADER_HEIGHT_PROFILE,
    "image_size": GAME_IMAGE_SIZE_PROFILE,
    "answer_box": GAME_ANSWER_BOX_PROFILE,
    "key_size": GAME_KEY_SIZE_PROFILE,
    "keyboard_pad": GAME_KEYBOARD_PAD_PROFILE,
    "definition_wrap": GAME_DEFINITION_WRAP_PROFILE,
    "action_button": GAME_ACTION_BUTTON_PROFILE,
    "wildcard_size": GAME_WILDCARD_SIZE_PROFILE,
    "container_pad": GAME_CONTAINER_PAD_PROFILE,
    "low_res": GAME_LOW_RES_SCALE_PROFILE,
}

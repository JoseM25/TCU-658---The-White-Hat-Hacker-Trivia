import customtkinter as ctk

GAME_BASE_DIMENSIONS = (1280, 720)
GAME_SCALE_LIMITS = (0.50, 2.20)  # Soporta 720p a 4K
GAME_RESIZE_DELAY = 80
GAME_GLOBAL_SCALE_FACTOR = 1.0


GAME_COLORS = {
    # Colores primarios
    "primary_blue": "#005DFF",
    "primary_hover": "#003BB8",
    # Colores de estado
    "success_green": "#00CFC5",
    "success_hover": "#009B94",
    "warning_yellow": "#FFC553",
    "warning_hover": "#CC9A42",
    "danger_red": "#FF4F60",
    "danger_hover": "#CC3F4D",
    # Colores de texto
    "text_dark": "#202632",
    "text_medium": "#3A3F4B",
    "text_light": "#7A7A7A",
    "text_white": "#FFFFFF",
    # Colores de fondo
    "bg_light": "#F5F7FA",
    "bg_card": "#FFFFFF",
    "bg_modal": "#202632",
    # Colores de borde
    "border_light": "#E2E7F3",
    "border_medium": "#D3DBEA",
    # Colores del encabezado
    "header_bg": "#202632",
    "header_hover": "#273246",
    # Colores del teclado
    "key_bg": "#E8ECF2",
    "key_hover": "#D0D6E0",
    "key_pressed": "#B8C0D0",
    # Colores de casillas de respuesta
    "answer_box_empty": "#E2E7F3",
    "answer_box_filled": "#D0D6E0",
    # Colores de retroalimentación
    "feedback_correct": "#00CFC5",
    "feedback_incorrect": "#FF4F60",
    # Colores de comodines
    "wildcard_x2": "#FFC553",
    "wildcard_x2_hover": "#E5B04A",
    "wildcard_x2_active": "#4CAF50",
    "wildcard_hint": "#00CFC5",
    "wildcard_hint_hover": "#00B5AD",
    "wildcard_freeze": "#005DFF",
    "wildcard_freeze_hover": "#0048CC",
    "wildcard_disabled": "#999999",
    # Colores de modales
    "modal_border": "#1D6CFF",
    "modal_cancel_bg": "#D0D6E0",
    "modal_cancel_hover": "#B8C0D0",
    "modal_skip_bg": "#FF4F60",
    "modal_skip_hover": "#CC3F4D",
    # Colores de insignias de nivel
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
    # Encabezado
    "header_height": 72,
    "header_pad_x": 24,
    "header_pad_y": 14,
    # Temporizador y puntaje
    "timer_icon_size": 16,
    "star_icon_size": 16,
    # Control de audio
    "audio_icon_base": 20,
    "audio_icon_min": 16,
    "audio_icon_max": 32,
    "audio_button_width": 30,
    "audio_button_height": 30,
    # Contenedor de pregunta
    "container_pad_x": 20,
    "container_pad_y": 8,
    "container_corner_radius": 14,
    # Imagen
    "image_base": 120,
    "image_min": 75,
    "image_max": 220,
    # Definición
    "definition_wrap_base": 600,
    "definition_wrap_min": 320,
    "definition_wrap_max": 1000,
    "info_icon_size": 24,
    # Casillas de respuesta
    "answer_box_base": 40,
    "answer_box_min": 28,
    "answer_box_max": 64,
    "answer_box_gap": 3,
    # Teclado
    "key_base": 40,
    "key_min": 30,
    "key_max": 68,
    "key_gap": 10,
    "key_row_gap": 3,
    "key_width_ratio": 1.2,
    "delete_key_width_ratio": 1.8,
    "keyboard_pad_x": 308,
    "keyboard_pad_y": 10,
    "delete_icon_base": 26,
    # Botones de acción
    "action_button_width": 130,
    "action_button_height": 38,
    "action_button_gap": 14,
    "action_corner_radius": 10,
    # Comodines
    "wildcard_size": 42,
    "wildcard_min": 32,
    "wildcard_max": 64,
    "wildcard_corner_radius": 21,
    "wildcard_gap": 4,
    "wildcard_font_size": 14,
    "charges_font_size": 12,
    "lightning_icon_size": 14,
    "freeze_icon_ratio": 0.5,
    # Retroalimentación
    "feedback_pad_bottom": 16,
}


GAME_FONT_SPECS = {
    # (family, base_size, weight, min_size)
    "timer": ("Poppins SemiBold", 24, "bold", 14),
    "score": ("Poppins ExtraBold", 28, "bold", 16),
    "definition": ("Open Sans Regular", 15, None, 5),
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


# Perfil de altura del encabezado (reducido ligeramente en resoluciones bajas)
GAME_HEADER_HEIGHT_PROFILE = [
    (720, 80),
    (900, 80),
    (1080, 80),
    (1280, 80),
    (1600, 100),
    (1920, 110),
    (2560, 130),
    (3200, 150),
    (3840, 170),
]

# Perfil de tamaño de imagen (reducido agresivamente en baja resolución)
GAME_IMAGE_SIZE_PROFILE = [
    (720, 200),
    (900, 200),
    (1080, 200),
    (1280, 200),
    (1600, 220),
    (1920, 250),
    (2560, 210),
    (3200, 250),
    (3840, 290),
]

# Perfil de tamaño de casillas de respuesta (reducido ligeramente en baja resolución)
GAME_ANSWER_BOX_PROFILE = [
    (720, 25),
    (900, 30),
    (1080, 35),
    (1280, 40),
    (1600, 45),
    (1920, 50),
    (2560, 36),
    (3200, 42),
    (3840, 48),
]

# Perfil de tamaño de teclas (reducido agresivamente en baja resolución)
GAME_KEY_SIZE_PROFILE = [
    (720, 60),
    (900, 65),
    (1080, 70),
    (1280, 75),
    (1600, 80),
    (1920, 85),
    (2560, 90),
    (3200, 95),
    (3840, 100),
]

# Perfil de escala del teclado (basado en altura) para mantener el teclado compacto
# Escalado menos agresivo para evitar desbordamiento en pantallas con DPI escalado
# (ej. 1080p al 125% da 864 píxeles lógicos pero no es realmente baja resolución)
GAME_KEYBOARD_SCALE_PROFILE = [
    (720, 0.90),
    (800, 0.90),
    (900, 0.90),
    (1080, 0.95),
    (1440, 1.00),
    (2160, 1.00),
]

# Perfil de relleno horizontal del teclado
GAME_KEYBOARD_PAD_PROFILE = [
    (720, 100),
    (900, 168),
    (1080, 220),
    (1280, 260),
    (1600, 320),
    (1920, 420),
    (2560, 560),
    (3200, 720),
    (3840, 840),
]

# Perfil de longitud de ajuste de definición - limitado para que el texto se ajuste bien
# Mayor longitud en alta resolución causa texto en una línea que se recorta
GAME_DEFINITION_WRAP_PROFILE = [
    (720, 400),
    (900, 400),
    (1080, 480),
    (1280, 560),
    (1600, 700),
    (1920, 840),
    (2560, 1120),
    (3200, 1400),
    (3840, 1680),
]

# Perfil de altura de scroll de definición
GAME_DEFINITION_HEIGHT_PROFILE = [
    (720, 50),
    (900, 60),
    (1080, 70),
    (1280, 80),
    (1600, 100),
    (1920, 120),
    (2560, 140),
    (3200, 160),
    (3840, 180),
]

# Perfiles de relleno del contenedor de definición
GAME_DEFINITION_PAD_X_PROFILE = [
    (720, 20),
    (900, 26),
    (1080, 32),
    (1280, 36),
    (1600, 44),
    (1920, 54),
    (2560, 68),
    (3200, 78),
    (3840, 88),
]

GAME_DEFINITION_PAD_Y_PROFILE = [
    (720, 6),
    (900, 8),
    (1080, 10),
    (1280, 12),
    (1600, 16),
    (1920, 21),
    (2560, 26),
    (3200, 30),
    (3840, 34),
]

# Perfil de ancho de botones de acción (reducido en baja resolución para más espacio)
GAME_ACTION_BUTTON_PROFILE = [
    (720, 90),
    (900, 115),
    (1080, 150),
    (1280, 160),
    (1600, 190),
    (1920, 220),
    (2560, 270),
    (3200, 320),
    (3840, 350),
]

# Perfil de tamaño de comodines (reducido en baja resolución)
GAME_WILDCARD_SIZE_PROFILE = [
    (720, 50),
    (900, 30),
    (1080, 35),
    (1280, 40),
    (1600, 45),
    (1920, 51),
    (2560, 90),
    (3200, 104),
    (3840, 112),
]

# Perfil de relleno del contenedor
GAME_CONTAINER_PAD_PROFILE = [
    (720, 10),
    (900, 10),
    (1080, 20),
    (1280, 24),
    (1600, 32),
    (1920, 40),
    (2560, 52),
    (3200, 64),
    (3840, 76),
]

# Perfil de penalización de escala para baja resolución
# Solo penalizar resoluciones POR DEBAJO de la altura base 720p
GAME_LOW_RES_SCALE_PROFILE = [
    (480, 0.70),
    (540, 0.80),
    (600, 0.90),
    (720, 1.00),
]


MODAL_BASE_SIZES = {
    # Modal de confirmación de saltar
    "skip_width": 400,
    "skip_height": 200,
    "skip_width_ratio": 0.35,
    "skip_height_ratio": 0.35,
    # Modal de resumen de pregunta
    "summary_width": 450,
    "summary_height": 380,
    "summary_width_ratio": 0.35,
    "summary_height_ratio": 0.48,
    "summary_max_scale": 1.6,
    # Modal de juego completado - altura aumentada para compatibilidad con 1080p
    "completion_width": 560,
    "completion_height": 520,
    "completion_width_ratio": 0.42,
    "completion_height_ratio": 0.62,
    # Común
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
        self.fonts = {}
        self.base_sizes = {}
        self.min_sizes = {}

        for name, (family, size, weight, min_size) in specs.items():
            font = (
                ctk.CTkFont(family=family, size=size, weight=weight)
                if weight
                else ctk.CTkFont(family=family, size=size)
            )
            self.fonts[name] = font
            self.base_sizes[name] = size
            self.min_sizes[name] = min_size or 10

    def get(self, name):
        return self.fonts.get(name)

    def items(self):
        return self.fonts.items()

    def update_scale(self, scale, scaler):
        for name, font in self.fonts.items():
            base_size = self.base_sizes.get(name, 14)
            min_size = self.min_sizes.get(name, 10)
            max_size = base_size * 2.5
            new_size = scaler.scale_value(base_size, scale, min_size, max_size)
            font.configure(size=new_size)

    def attach_attributes(self, target):
        for name, font in self.fonts.items():
            setattr(target, f"{name}_font", font)


class GameSizeCalculator:

    # Umbral de altura por debajo del cual aplicamos tamaño compacto
    # Incluye 720p (720), 768p (768) y pantallas 1080p con DPI escalado
    # (1080p al 125% da ~864 píxeles lógicos, al 150% da ~720)
    HEIGHT_CONSTRAINED_THRESHOLD = 800

    def __init__(self, scaler, profiles):
        self.scaler = scaler
        self.profiles = profiles

    def apply_compact_scale(self, value, scale, min_value=None):
        if scale >= 1.0:
            return value
        scaled = int(round(value * scale))
        if min_value is not None:
            scaled = max(min_value, scaled)
        return scaled

    def calculate_sizes(self, scale, window_width, window_height):
        s = self.scaler.scale_value
        ip = self.scaler.interpolate_profile

        sizes = {}

        # Determinar si estamos limitados por altura (720p o pantallas de altura baja)
        # Solo aplicar tamaño compacto cuando la altura esté realmente limitada
        is_height_constrained = window_height <= self.HEIGHT_CONSTRAINED_THRESHOLD

        # Para pantallas limitadas por altura, usar la dimensión menor (altura) para
        # buscar perfiles de elementos que necesitan ajustarse verticalmente
        # Esto asegura tamaño correcto en 720p (1280x720) donde la altura es la limitante
        vertical_dimension = (
            min(window_width, window_height) if is_height_constrained else window_width
        )

        # Encabezado - usar altura para búsqueda cuando está limitado para escalar naturalmente
        # Esto da reducción gradual en vez de un salto repentino
        header_lookup_dim = (
            min(window_width, window_height) if is_height_constrained else window_width
        )
        sizes["header_height"] = ip(header_lookup_dim, self.profiles["header_height"])
        sizes["header_pad_x"] = s(GAME_BASE_SIZES["header_pad_x"], scale, 16, 72)
        sizes["header_pad_y"] = s(GAME_BASE_SIZES["header_pad_y"], scale, 12, 48)

        # Iconos de temporizador y puntaje
        sizes["timer_icon"] = s(GAME_BASE_SIZES["timer_icon_size"], scale, 16, 40)
        sizes["star_icon"] = s(GAME_BASE_SIZES["star_icon_size"], scale, 16, 40)

        # Botón de audio
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

        # Contenedor de pregunta
        sizes["container_pad_x"] = ip(window_width, self.profiles["container_pad"])
        sizes["container_pad_y"] = s(GAME_BASE_SIZES["container_pad_y"], scale, 8, 50)
        sizes["container_corner_radius"] = s(
            GAME_BASE_SIZES["container_corner_radius"], scale, 12, 36
        )

        # Imagen - usa vertical_dimension si hay restricción de altura, sino ancho
        sizes["image_size"] = ip(vertical_dimension, self.profiles["image_size"])

        # Definición - siempre usar ancho para wraplength (restricción horizontal)
        sizes["definition_wrap"] = ip(window_width, self.profiles["definition_wrap"])
        sizes["definition_height"] = ip(
            window_height, self.profiles["definition_height"]
        )
        sizes["definition_pad_x"] = ip(window_width, self.profiles["definition_pad_x"])
        sizes["definition_pad_y"] = ip(window_height, self.profiles["definition_pad_y"])
        sizes["info_icon"] = s(GAME_BASE_SIZES["info_icon_size"], scale, 16, 40)

        # Cajas de respuesta - usa vertical_dimension si hay restricción de altura
        sizes["answer_box"] = ip(vertical_dimension, self.profiles["answer_box"])
        sizes["answer_box_gap"] = s(GAME_BASE_SIZES["answer_box_gap"], scale, 2, 6)

        # Teclado - tamaños de tecla usan vertical_dimension, relleno usa ancho
        sizes["key_size"] = ip(vertical_dimension, self.profiles["key_size"])
        sizes["key_gap"] = s(GAME_BASE_SIZES["key_gap"], scale, 4, 24)
        sizes["key_row_gap"] = s(GAME_BASE_SIZES["key_row_gap"], scale, 2, 8)
        sizes["keyboard_pad"] = ip(window_width, self.profiles["keyboard_pad"])
        sizes["keyboard_pad_y"] = s(GAME_BASE_SIZES["keyboard_pad_y"], scale, 8, 32)
        sizes["key_width_ratio"] = GAME_BASE_SIZES.get("key_width_ratio", 1.0)
        sizes["delete_key_width_ratio"] = GAME_BASE_SIZES.get(
            "delete_key_width_ratio", 1.8
        )
        sizes["delete_icon"] = s(GAME_BASE_SIZES["delete_icon_base"], scale, 16, 48)

        # Botones de acción - usa vertical_dimension si hay restricción de altura
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

        # Comodines - usa vertical_dimension si hay restricción de altura
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

        # Retroalimentación
        sizes["feedback_pad_bottom"] = s(
            GAME_BASE_SIZES["feedback_pad_bottom"], scale, 8, 48
        )

        # Almacenar escala y dimensiones
        sizes["scale"] = scale
        sizes["window_width"] = window_width
        sizes["window_height"] = window_height
        sizes["is_height_constrained"] = is_height_constrained

        # Si la altura real está por debajo de la base 720p, reducir tamaños basados en perfil
        # para evitar desbordamiento de contenido
        if is_height_constrained and scale < 1.0:
            compact_scale = scale
            sizes["header_height"] = self.apply_compact_scale(
                sizes["header_height"], compact_scale, min_value=44
            )
            sizes["image_size"] = self.apply_compact_scale(
                sizes["image_size"],
                compact_scale,
                min_value=GAME_BASE_SIZES["image_min"],
            )
            sizes["answer_box"] = self.apply_compact_scale(
                sizes["answer_box"], compact_scale, min_value=24
            )
            sizes["key_size"] = self.apply_compact_scale(
                sizes["key_size"], compact_scale, min_value=20
            )
            sizes["key_gap"] = self.apply_compact_scale(
                sizes["key_gap"], compact_scale, min_value=3
            )
            sizes["key_row_gap"] = self.apply_compact_scale(
                sizes["key_row_gap"], compact_scale, min_value=1
            )
            sizes["keyboard_pad_y"] = self.apply_compact_scale(
                sizes["keyboard_pad_y"], compact_scale, min_value=4
            )
            sizes["delete_icon"] = self.apply_compact_scale(
                sizes["delete_icon"], compact_scale, min_value=12
            )
            sizes["wildcard_size"] = self.apply_compact_scale(
                sizes["wildcard_size"], compact_scale, min_value=24
            )
            sizes["wildcard_corner_radius"] = sizes["wildcard_size"] // 2
            sizes["freeze_icon"] = int(
                sizes["wildcard_size"] * GAME_BASE_SIZES["freeze_icon_ratio"]
            )

        return sizes


GAME_PROFILES = {
    "header_height": GAME_HEADER_HEIGHT_PROFILE,
    "image_size": GAME_IMAGE_SIZE_PROFILE,
    "answer_box": GAME_ANSWER_BOX_PROFILE,
    "key_size": GAME_KEY_SIZE_PROFILE,
    "keyboard_scale": GAME_KEYBOARD_SCALE_PROFILE,
    "keyboard_pad": GAME_KEYBOARD_PAD_PROFILE,
    "definition_wrap": GAME_DEFINITION_WRAP_PROFILE,
    "definition_height": GAME_DEFINITION_HEIGHT_PROFILE,
    "definition_pad_x": GAME_DEFINITION_PAD_X_PROFILE,
    "definition_pad_y": GAME_DEFINITION_PAD_Y_PROFILE,
    "action_button": GAME_ACTION_BUTTON_PROFILE,
    "wildcard_size": GAME_WILDCARD_SIZE_PROFILE,
    "container_pad": GAME_CONTAINER_PAD_PROFILE,
    "low_res": GAME_LOW_RES_SCALE_PROFILE,
}

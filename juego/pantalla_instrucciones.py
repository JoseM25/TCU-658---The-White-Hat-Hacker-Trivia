from tkinter import TclError

import customtkinter as ctk
from PIL import Image, ImageTk
from tksvg import SvgImage as TkSvgImage

from juego.rutas_app import get_resource_images_dir


class InstructionsScreen:
    BASE_DIMENSIONS = (1280, 720)
    BASE_FONT_SIZES = {
        "title": 48,
        "section_title": 24,
        "body": 10,
        "button": 24,
        "toggle": 16,
        "icon": 16,
    }
    SCALE_LIMITS = (0.50, 1.75)
    RESIZE_DELAY = 80
    SVG_RASTER_SCALE = 2.0

    BASE_LOGO_SIZE = 90
    LOGO_MIN_SIZE = 48
    LOGO_MAX_SIZE = 180

    CARD_BASE_WIDTH = 900
    CARD_MIN_WIDTH = 360
    CARD_MAX_WIDTH = 1400

    ICON_BASE_SIZE = 32
    ICON_MIN_SIZE = 24
    ICON_MAX_SIZE = 80

    TOGGLE_WIDTH_BASE = 76
    TOGGLE_HEIGHT_BASE = 34

    WRAP_BASE = 600
    WRAP_MIN = 300
    WRAP_MAX = 1200
    WRAP_MAX_FRACTION = 0.78
    WRAP_FILL = 0.78
    WRAP_SMALL_FRACTION = 0.78
    WRAP_SMALL_FILL = 0.78

    HEADER_PAD_BASE = 32
    CARD_PAD_BASE = 24
    SECTION_PAD_BASE = 18
    BUTTON_PAD_TOP_BASE = 16
    BUTTON_PAD_BOTTOM_BASE = 32
    TITLE_BODY_GAP_BASE = 6

    LANGUAGE_ORDER = ("EN", "ES")

    SECTION_CONFIGS = [
        {"key": "objective", "icon": "target.svg", "fallback": "OBJ"},
        {"key": "how_to_play", "icon": "keyboard.svg", "fallback": "PLAY"},
        {"key": "scoring", "icon": "star.svg", "fallback": "PTS"},
    ]
    ICON_TINT_COLOR = "#005DFF"

    LANGUAGE_CONTENT = {
        "EN": {
            "title": "How to Play",
            "return_button": "Main Menu",
            "sections": {
                "objective": {
                    "title": "Objective",
                    "body": [
                        "The primary goal is for students to identify and "
                        "match definitions related to Ethical hacking with "
                        "their respective vocabulary terms. This will be aided "
                        "by images and audio. Additionally, the teachers can "
                        "introduce new definitions and vocabulary terms.",
                    ],
                },
                "how_to_play": {
                    "title": "How to Play",
                    "body": [
                        "When the game starts, a definition of an Ethical Hacking "
                        "hacking concept will appear on the screen. Each definition "
                        "includes both an image and an audio explanation to facilitate "
                        "better understanding.",
                        "A series of spaces corresponding to the length of the word to "
                        "be guessed will be displayed, with each space representing a letter. "
                        "A virtual keyboard will be provided for letter input. The screen will "
                        "also show a timer, wildcard options, and your total score.",
                        "To enter your answer, select letters using the virtual keyboard to "
                        "fill in the provided spaces, then press the button to check your "
                        "response. Answers cannot be verified until all spaces for the "
                        "word are filled.",
                    ],
                },
                "scoring": {
                    "title": "Scoring",
                    "body": [
                        "If your answer is incorrect, the game will notify you, and you can "
                        "try again. If correct, your earned points and total score will be "
                        "displayed. If you're unsure of the answer, you can skip the "
                        "word; the correct answer will be revealed, but no points will be "
                        "awarded. Your total score is calculated based on how quickly you "
                        "provide the correct answer and the number of mistakes made.",
                        "Achieving higher scores unlocks wildcards or lifelines (such as "
                        "score multipliers, letter reveals, and time freezes) to assist you in "
                        "guessing subsequent words, helping you achieve higher overall scores.",
                        "At the end of the game, after answering all questions, a final screen "
                        "will display your total score and your knowledge level on the topic "
                        "(beginner, student, professional, expert, master).",
                    ],
                },
            },
        },
        "ES": {
            "title": "Cómo Jugar",
            "return_button": "Menú Principal",
            "sections": {
                "objective": {
                    "title": "Objetivo",
                    "body": [
                        "El objetivo principal es que los y las estudiantes identifiquen "
                        "y emparejen definiciones relacionadas con el Hacking Ético con sus "
                        "respectivos términos de vocabulario. Esto se verá facilitado por "
                        "imágenes y audio. Además, los docentes pueden introducir nuevas "
                        "definiciones y términos de vocabulario.",
                    ],
                },
                "how_to_play": {
                    "title": "Cómo Jugar",
                    "body": [
                        "Cuando el juego comience, aparecerá en pantalla una definición "
                        "de un concepto de Hacking Ético. Cada definición incluirá una "
                        "imagen y una explicación en audio para facilitar una mejor "
                        "comprensión.",
                        "Se mostrará una serie de espacios correspondientes "
                        "a la longitud de la palabra que se debe adivinar, donde cada "
                        "espacio representa una letra. Se proporcionará un teclado "
                        "virtual para la entrada de letras. La pantalla también mostrará "
                        "un temporizador, opciones de comodín y tu puntuación total.",
                        "Para ingresar tu respuesta, selecciona letras usando el "
                        "teclado virtual para llenar los espacios proporcionados y luego "
                        "presiona el botón para verificar tu respuesta. Las respuestas no "
                        "pueden ser verificadas hasta que todos los espacios de la palabra "
                        "estén llenos.",
                    ],
                },
                "scoring": {
                    "title": "Puntaje",
                    "body": [
                        "Si la respuesta es incorrecta, el juego indicará que ha cometido "
                        "un error y podrás intentarlo nuevamente. Si es correcta, se "
                        "mostrarán la puntuación obtenida y el puntaje total acumulado. "
                        "Si desconoces la respuesta, puedes saltar la palabra; la respuesta "
                        "correcta será revelada, pero no se otorgarán puntos. La puntuación "
                        "total se calcula en función de la rapidez con la que se proporciona "
                        "la respuesta correcta y el número de errores cometidos.",
                        "Lograr puntuaciones más altas desbloquea comodines o salvavidas "
                        "(como multiplicadores de puntuación, revelaciones de letras y "
                        "congelaciones de temporizador) que facilitarán adivinar las palabras "
                        "posteriores y mejorar así tu puntaje general.",
                        "Al final del juego, después de responder todas las preguntas, una "
                        "pantalla final mostrará tu puntuación total y tu nivel de "
                        "conocimiento sobre el tema (principiante, estudiante, profesional, "
                        "experto, maestro).",
                    ],
                },
            },
        },
    }

    def __init__(self, parent, on_return_callback=None):
        self.parent = parent
        self.on_return_callback = on_return_callback
        self.language = "EN"

        self.resize_job = None
        self.logo_image = None
        self.title_label = None
        self.toggle_container = None
        self.card_container = None
        self.instructions_card = None
        self.return_button = None
        self.header_frame = None
        self.button_container = None
        self.logo_label = None

        self.section_widgets = {}
        self.toggle_buttons = {}

        self.images_dir = get_resource_images_dir()
        self.logo_svg_path = self.images_dir / "Hat.svg"

        self.title_font = ctk.CTkFont(
            family="Poppins ExtraBold",
            size=self.BASE_FONT_SIZES["title"],
            weight="bold",
        )
        self.section_title_font = ctk.CTkFont(
            family="Poppins SemiBold", size=self.BASE_FONT_SIZES["section_title"]
        )
        self.body_font = ctk.CTkFont(
            family="Open Sans Regular", size=self.BASE_FONT_SIZES["body"]
        )
        self.button_font = ctk.CTkFont(
            family="Poppins SemiBold", size=self.BASE_FONT_SIZES["button"]
        )
        self.toggle_font = ctk.CTkFont(
            family="Poppins SemiBold",
            size=self.BASE_FONT_SIZES["toggle"],
            weight="bold",
        )
        self.icon_font = ctk.CTkFont(
            family="Poppins Bold", size=self.BASE_FONT_SIZES["icon"], weight="bold"
        )

        self.build_ui()
        self.update_language()
        self.parent.bind("<Configure>", self.on_resize)
        self.apply_responsive()

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
        self.main.grid_columnconfigure(0, weight=1)

        self.build_header()
        self.build_card()
        self.build_footer()

    def build_header(self):
        self.header_frame = ctk.CTkFrame(self.main, fg_color="transparent")
        self.header_frame.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=self.HEADER_PAD_BASE,
            pady=(self.HEADER_PAD_BASE, self.HEADER_PAD_BASE // 2),
        )
        self.header_frame.grid_columnconfigure(0, weight=0)
        self.header_frame.grid_columnconfigure(1, weight=1)
        self.header_frame.grid_columnconfigure(2, weight=0)

        logo_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        logo_frame.grid(row=0, column=0, sticky="w")

        img = self.load_svg_image(self.logo_svg_path, scale=self.SVG_RASTER_SCALE)
        if img:
            self.logo_image = ctk.CTkImage(
                light_image=img,
                dark_image=img,
                size=(self.BASE_LOGO_SIZE, self.BASE_LOGO_SIZE),
            )
            self.logo_label = ctk.CTkLabel(logo_frame, image=self.logo_image, text="")
        else:
            self.logo_label = ctk.CTkLabel(
                logo_frame,
                text="Logo",
                font=ctk.CTkFont(size=16),
                text_color="red",
            )
        self.logo_label.grid(row=0, column=0, sticky="w")

        title_container = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        title_container.grid(row=0, column=1, sticky="nsew", padx=12)
        title_container.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(
            title_container,
            text="",
            font=self.title_font,
            text_color="#202632",
            anchor="center",
        )
        self.title_label.grid(row=0, column=0, sticky="n")

        self.toggle_container = ctk.CTkFrame(
            self.header_frame,
            fg_color="#F5F7FA",
            border_color="#D3DBEA",
            border_width=1,
            corner_radius=18,
        )
        self.toggle_container.grid(row=0, column=2, sticky="e")

        for column, lang in enumerate(self.LANGUAGE_ORDER):
            button = ctk.CTkButton(
                self.toggle_container,
                text=lang,
                font=self.toggle_font,
                width=self.TOGGLE_WIDTH_BASE,
                height=self.TOGGLE_HEIGHT_BASE,
                fg_color="transparent",
                hover_color=self.parent.cget("fg_color"),
                command=lambda value=lang: self.set_language(value),
            )
            button.grid(row=0, column=column, padx=4, pady=4, sticky="nsew")
            self.toggle_container.grid_columnconfigure(column, weight=1)
            self.toggle_buttons[lang] = button

    def build_card(self):
        self.card_container = ctk.CTkFrame(self.main, fg_color="transparent")
        self.card_container.grid(
            row=1, column=0, sticky="nsew", padx=self.CARD_PAD_BASE, pady=(0, 16)
        )
        self.card_container.grid_columnconfigure(0, weight=1)
        self.card_container.grid_rowconfigure(0, weight=1)

        self.instructions_card = ctk.CTkFrame(
            self.card_container,
            fg_color="transparent",
            corner_radius=24,
            border_color="#E2E7F3",
            border_width=1,
        )
        self.instructions_card.grid(row=0, column=0, sticky="nsew")
        self.instructions_card.grid_columnconfigure(0, weight=1)

        self.section_widgets.clear()

        for row, config in enumerate(self.SECTION_CONFIGS):
            section_frame = ctk.CTkFrame(self.instructions_card, fg_color="transparent")
            section_frame.grid(
                row=row,
                column=0,
                sticky="ew",
                padx=self.CARD_PAD_BASE,
                pady=(0, self.SECTION_PAD_BASE),
            )
            section_frame.grid_columnconfigure(0, weight=0)
            section_frame.grid_columnconfigure(1, weight=1)

            icon_frame = ctk.CTkFrame(
                section_frame,
                fg_color="#F5F7FA",
                corner_radius=18,
                width=self.ICON_BASE_SIZE,
                height=self.ICON_BASE_SIZE,
            )
            icon_frame.grid(row=0, column=0, rowspan=2, sticky="nw")
            icon_frame.grid_propagate(False)

            icon_image = None
            svg_path = self.images_dir / config["icon"]
            tint_color = self.ICON_TINT_COLOR if config["icon"] == "star.svg" else None
            svg_image = self.load_svg_image(
                svg_path, scale=self.SVG_RASTER_SCALE, tint_color=tint_color
            )
            if svg_image:
                icon_image = ctk.CTkImage(
                    light_image=svg_image,
                    dark_image=svg_image,
                    size=(self.ICON_BASE_SIZE, self.ICON_BASE_SIZE),
                )
                icon_label = ctk.CTkLabel(icon_frame, image=icon_image, text="")
            else:
                icon_label = ctk.CTkLabel(
                    icon_frame,
                    text=config.get("fallback", config["key"].upper()),
                    font=self.icon_font,
                    text_color="#FFFFFF",
                )
            icon_label.place(relx=0.5, rely=0.5, anchor="center")

            title_label = ctk.CTkLabel(
                section_frame,
                text="",
                font=self.section_title_font,
                text_color="#202632",
                anchor="w",
            )
            title_label.grid(row=0, column=1, sticky="nw", padx=(16, 6))

            body_label = ctk.CTkLabel(
                section_frame,
                text="",
                font=self.body_font,
                text_color="#3A3F4B",
                justify="left",
                anchor="w",
                wraplength=self.WRAP_BASE,
            )
            body_label.grid(
                row=1,
                column=1,
                sticky="nwe",
                padx=(16, 6),
                pady=(self.TITLE_BODY_GAP_BASE, 0),
            )

            self.section_widgets[config["key"]] = {
                "frame": section_frame,
                "icon_frame": icon_frame,
                "icon_label": icon_label,
                "icon_image": icon_image,
                "title": title_label,
                "body": body_label,
            }

    def build_footer(self):
        self.button_container = ctk.CTkFrame(self.main, fg_color="transparent")
        self.button_container.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=self.CARD_PAD_BASE,
            pady=(self.BUTTON_PAD_TOP_BASE, self.BUTTON_PAD_BOTTOM_BASE),
        )
        self.button_container.grid_columnconfigure(0, weight=1)

        self.return_button = ctk.CTkButton(
            self.button_container,
            text="",
            font=self.button_font,
            fg_color="#005DFF",
            hover_color="#003BB8",
            command=self.return_to_menu,
            height=48,
            width=220,
        )
        self.return_button.grid(row=0, column=0, pady=0)

    def update_language(self):
        content = self.LANGUAGE_CONTENT.get(self.language, self.LANGUAGE_CONTENT["EN"])
        self.title_label.configure(text=content["title"])
        self.return_button.configure(text=content["return_button"])

        sections = content["sections"]
        bullet = "\u2022"
        for config in self.SECTION_CONFIGS:
            data = sections.get(config["key"], {})
            title_text = data.get("title", "")
            body_lines = data.get("body", [])
            body_text = "\n".join(f"{bullet} {line.strip()}" for line in body_lines)

            widget = self.section_widgets.get(config["key"])
            if widget:
                widget["title"].configure(text=title_text)
                widget["body"].configure(text=body_text)

        self.update_toggle_styles()

    def set_language(self, language):
        if language not in self.LANGUAGE_ORDER:
            return
        if language == self.language:
            return
        self.language = language
        self.update_language()

    def update_toggle_styles(self):
        for lang, button in self.toggle_buttons.items():
            if lang == self.language:
                button.configure(text_color="#005DFF")
            else:
                button.configure(text_color="#7A7A7A")

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

        self.title_font.configure(
            size=int(max(18, self.BASE_FONT_SIZES["title"] * scale))
        )
        self.section_title_font.configure(
            size=int(max(10, self.BASE_FONT_SIZES["section_title"] * scale))
        )
        self.body_font.configure(size=int(max(6, self.BASE_FONT_SIZES["body"] * scale)))
        self.button_font.configure(
            size=int(max(12, self.BASE_FONT_SIZES["button"] * scale))
        )
        self.toggle_font.configure(
            size=int(max(9, self.BASE_FONT_SIZES["toggle"] * scale))
        )
        self.icon_font.configure(
            size=int(max(10, self.BASE_FONT_SIZES["icon"] * scale))
        )

        if self.logo_image:
            desired = int(
                max(
                    self.LOGO_MIN_SIZE,
                    min(self.LOGO_MAX_SIZE, self.BASE_LOGO_SIZE * scale),
                )
            )
            self.logo_image.configure(size=(desired, desired))

        header_pad = int(max(16, min(64, self.HEADER_PAD_BASE * scale)))
        header_bottom = int(max(10, min(32, header_pad * 0.6)))
        self.header_frame.grid_configure(
            padx=header_pad, pady=(header_pad, header_bottom)
        )

        toggle_width = int(max(42, min(160, self.TOGGLE_WIDTH_BASE * scale)))
        toggle_height = int(max(24, min(60, self.TOGGLE_HEIGHT_BASE * scale)))
        for button in self.toggle_buttons.values():
            button.configure(width=toggle_width, height=toggle_height)

        card_pad = int(max(12, min(40, self.CARD_PAD_BASE * scale)))
        target_card_width = int(
            min(
                self.CARD_MAX_WIDTH,
                max(self.CARD_MIN_WIDTH, self.CARD_BASE_WIDTH * scale),
            )
        )
        card_padx = max(card_pad, (width - target_card_width) // 2)
        self.card_container.grid_configure(padx=card_padx)

        inner_pad = int(max(14, min(48, self.CARD_PAD_BASE * scale)))
        section_gap = int(max(10, min(30, self.SECTION_PAD_BASE * scale)))

        icon_size = int(
            max(
                self.ICON_MIN_SIZE,
                min(self.ICON_MAX_SIZE, self.ICON_BASE_SIZE * scale),
            )
        )

        icon_block = icon_size + 16
        available = target_card_width - (inner_pad * 2) - icon_block

        small_screen = scale <= 0.75

        if small_screen:
            wrap_by_available = int(available * self.WRAP_SMALL_FILL)
            wrap_by_fraction = int(target_card_width * self.WRAP_SMALL_FRACTION)
        else:
            wrap_by_available = int(available * self.WRAP_FILL)
            wrap_by_fraction = int(target_card_width * self.WRAP_MAX_FRACTION)

        wrap_length = int(
            max(
                self.WRAP_MIN,
                min(self.WRAP_MAX, wrap_by_available, wrap_by_fraction),
            )
        )

        for index, config in enumerate(self.SECTION_CONFIGS):
            widget = self.section_widgets.get(config["key"])
            if not widget:
                continue

            is_first = index == 0
            is_last = index == len(self.SECTION_CONFIGS) - 1

            if small_screen:
                top_pad = section_gap
                bottom_pad = section_gap
            else:
                top_pad = inner_pad if is_first else section_gap
                bottom_pad = inner_pad if is_last else section_gap

            widget["frame"].grid_configure(padx=inner_pad, pady=(top_pad, bottom_pad))
            widget["icon_frame"].configure(width=icon_size, height=icon_size)
            if widget["icon_image"]:
                widget["icon_image"].configure(size=(icon_size, icon_size))
            else:
                widget["icon_label"].configure(font=self.icon_font)
            widget["body"].configure(wraplength=wrap_length)

        button_pad_top = int(max(10, min(40, self.BUTTON_PAD_TOP_BASE * scale)))
        button_pad_bottom = int(max(18, min(72, self.BUTTON_PAD_BOTTOM_BASE * scale)))
        self.button_container.grid_configure(
            padx=card_padx,
            pady=(button_pad_top, button_pad_bottom),
        )

        button_width = int(max(160, min(320, 220 * scale)))
        button_height = int(max(32, min(72, 50 * scale)))
        self.return_button.configure(width=button_width, height=button_height)

        self.resize_job = None

    def cleanup(self):
        """Clean up resources before switching screens."""
        try:
            self.parent.unbind("<Configure>")
        except TclError:
            pass
        if self.resize_job:
            try:
                self.parent.after_cancel(self.resize_job)
            except TclError:
                pass
            self.resize_job = None

    def return_to_menu(self):
        self.cleanup()
        if self.on_return_callback:
            self.on_return_callback()

    def tint_image(self, pil_image, hex_color):
        if not hex_color:
            return pil_image
        try:
            hex_color = hex_color.lstrip("#")
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
        except (AttributeError, ValueError, IndexError):
            return pil_image
        alpha = pil_image.split()[-1]
        tinted = Image.new("RGBA", pil_image.size, (r, g, b, 0))
        tinted.putalpha(alpha)
        return tinted

    def load_svg_image(self, svg_path, scale=1.0, tint_color=None):
        try:
            svg_photo = TkSvgImage(file=str(svg_path), scale=scale)
            pil_image = ImageTk.getimage(svg_photo).convert("RGBA")
            return self.tint_image(pil_image, tint_color)
        except (FileNotFoundError, ValueError) as error:
            print(f"Error loading SVG image '{svg_path}': {error}")
            return None

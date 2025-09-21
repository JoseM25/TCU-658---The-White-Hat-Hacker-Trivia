import os
import customtkinter as ctk
from PIL import ImageTk
from tksvg import SvgImage as TkSvgImage


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
    BASE_LOGO_SIZE = 88
    LOGO_MIN_SIZE = 40
    LOGO_MAX_SIZE = 180
    SCALE_LIMITS = (0.45, 1.75)
    RESIZE_DELAY = 80

    CARD_BASE_WIDTH = 920
    CARD_MIN_WIDTH = 360
    CARD_MAX_WIDTH = 1560
    CARD_PADDING_BASE = 32
    SECTION_TOP_PAD_BASE = 8
    SECTION_BOTTOM_PAD_BASE = 18

    ICON_BASE_SIZE = 25
    ICON_MIN_SIZE = 10
    ICON_MAX_SIZE = 96

    TOGGLE_WIDTH_BASE = 76
    TOGGLE_HEIGHT_BASE = 34

    HEADER_HORIZONTAL_PAD_BASE = 32
    HEADER_TOP_PAD_BASE = 22
    HEADER_BOTTOM_PAD_BASE = 16

    BUTTON_TOP_PAD_BASE = 16
    BUTTON_BOTTOM_PAD_BASE = 30

    LANGUAGE_ORDER = ("EN", "ES")

    def __init__(self, parent, on_return_callback=None):
        self.parent = parent
        self.on_return_callback = on_return_callback
        self.language = "EN"

        self.logo_image = None
        self.logo_label = None
        self.title_label = None
        self.toggle_container = None
        self.toggle_buttons = {}
        self.card_container = None
        self.instructions_card = None
        self.section_widgets = {}
        self.section_frames = []
        self.return_button = None
        self.resize_job = None
        self.header_frame = None
        self.button_container = None
        self.lang_dividers = []

        self.images_dir = os.path.join("recursos", "imagenes")
        self.section_configs = [
            {
                "key": "objective",
                "icon_svg": os.path.join(self.images_dir, "target.svg"),
                "fallback_text": "OBJ",
            },
            {
                "key": "how_to_play",
                "icon_svg": os.path.join(self.images_dir, "keyboard.svg"),
                "fallback_text": "PLAY",
            },
            {
                "key": "scoring",
                "icon_svg": os.path.join(self.images_dir, "star.svg"),
                "fallback_text": "PTS",
            },
        ]

        self.language_content = {
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
                            "espacio representando una letra. Se proporcionara un teclado "
                            "virtual para la entrada de letras. La pantalla también mostrará "
                            "un temporizador, opciones de comodín y tu puntuación total.",
                            "Para ingresar su respuesta, seleccione letras usando el "
                            "teclado virtual para llenar los espacios proporcionados y luego "
                            "presione el botón para verificar su respuesta. Las respuestas no "
                            "pueden ser verificadas hasta que todos los espacios de la palabra "
                            "estén llenos.",
                        ],
                    },
                    "scoring": {
                        "title": "Puntaje",
                        "body": [
                            "Si la respuesta es incorrecta, el juego indicará que ha cometido "
                            "un error y podrá intentarlo nuevamente. Si es correcta, se "
                            "mostrarán la puntuación obtenida y el puntaje total acumulado. "
                            "Si desconoce la respuesta, puede saltar la palabra; la respuesta "
                            "correcta será revelada, pero no se otorgarán puntos. La puntuación "
                            "total se calcula en función de la rapidez con la que se proporciona "
                            "la respuesta correcta y el número de errores cometidos.",
                            "Lograr puntuaciones más altas desbloquea comodines o salvavidas "
                            "(como multiplicadores de puntuación, revelaciones de letras y "
                            "congelaciones de temporizador) que facilitarán adivinar las palabras "
                            "posteriores y mejorar así su puntaje general. ",
                            "Al final del juego, después de responder todas las preguntas, una "
                            "pantalla final mostrará su puntuación total y su nivel de "
                            "conocimiento sobre el tema (principiante, estudiante, profesional, "
                            "experto, maestro).",
                        ],
                    },
                },
            },
        }

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

        self.logo_svg_path = os.path.join(self.images_dir, "Hat.svg")

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
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 16))
        self.header_frame.grid_columnconfigure(0, weight=0)
        self.header_frame.grid_columnconfigure(1, weight=1)
        self.header_frame.grid_columnconfigure(2, weight=0)

        logo_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        logo_frame.grid(row=0, column=0, sticky="nw")

        img = self.load_svg_image(self.logo_svg_path, scale=2.0)
        if img:
            self.logo_image = ctk.CTkImage(
                light_image=img,
                dark_image=img,
                size=(self.BASE_LOGO_SIZE, self.BASE_LOGO_SIZE),
            )
            self.logo_label = ctk.CTkLabel(logo_frame, image=self.logo_image, text="")
            self.logo_label.grid(row=0, column=0, sticky="nw")
        else:
            self.logo_label = ctk.CTkLabel(
                logo_frame,
                text="Logo",
                font=ctk.CTkFont(size=16),
                text_color="red",
            )
            self.logo_label.grid(row=0, column=0, sticky="nw")

        title_container = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        title_container.grid(row=0, column=1, sticky="n", padx=12)
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
        self.toggle_container.grid(row=0, column=2, sticky="ne", padx=(12, 0))

        for idx, lang in enumerate(self.LANGUAGE_ORDER):
            col_idx = idx * 2
            if idx > 0:
                divider = ctk.CTkLabel(
                    self.toggle_container,
                    text="|",
                    font=self.toggle_font,
                    text_color="#202632",
                )
                divider.grid(row=0, column=col_idx - 1, sticky="ns", padx=6, pady=6)
                self.toggle_container.grid_columnconfigure(
                    col_idx - 1, weight=0, minsize=1
                )
                self.lang_dividers.append(divider)

            button = ctk.CTkButton(
                self.toggle_container,
                text=lang,
                font=self.toggle_font,
                width=self.TOGGLE_WIDTH_BASE,
                height=self.TOGGLE_HEIGHT_BASE,
                text_color="#202632",
                command=lambda value=lang: self.set_language(value),
                fg_color="transparent",
                hover_color=self.parent.cget("fg_color"),
            )
            button.grid(
                row=0,
                column=col_idx,
                sticky="nsew",
                padx=4,
                pady=4,
            )
            self.toggle_container.grid_columnconfigure(col_idx, weight=1)
            self.toggle_buttons[lang] = button

    def build_card(self):
        self.card_container = ctk.CTkFrame(self.main, fg_color="transparent")
        self.card_container.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 12))
        self.card_container.grid_columnconfigure(0, weight=1)
        self.card_container.grid_rowconfigure(0, weight=1)

        self.instructions_card = ctk.CTkFrame(
            self.card_container,
            fg_color="transparent",
            corner_radius=24,
            border_color="#E2E7F3",
            border_width=1,
        )
        self.instructions_card.grid(row=0, column=0, sticky="nsew", pady=0)
        self.instructions_card.grid_columnconfigure(0, weight=1)

        self.section_widgets.clear()
        self.section_frames.clear()

        for index, config in enumerate(self.section_configs):
            section_frame = ctk.CTkFrame(self.instructions_card, fg_color="transparent")
            section_frame.grid(
                row=index, column=0, sticky="nsew", padx=self.CARD_PADDING_BASE
            )
            section_frame.grid_columnconfigure(0, weight=0)
            section_frame.grid_columnconfigure(1, weight=1)
            section_frame.grid_rowconfigure(1, weight=1)

            icon_frame = ctk.CTkFrame(
                section_frame,
                fg_color="transparent",
                corner_radius=18,
                width=self.ICON_BASE_SIZE,
                height=self.ICON_BASE_SIZE,
            )
            icon_frame.grid(row=0, column=0, rowspan=2, sticky="nw")
            icon_frame.grid_propagate(False)

            icon_image = None
            svg_path = config.get("icon_svg")
            if svg_path:
                svg_image = self.load_svg_image(svg_path, scale=2.0)
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
                        text=config.get("fallback_text", config["key"].upper()),
                        font=self.icon_font,
                        text_color="#FFFFFF",
                    )
            else:
                icon_label = ctk.CTkLabel(
                    icon_frame,
                    text=config.get("fallback_text", config["key"].upper()),
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
            title_label.grid(row=0, column=1, sticky="nw", padx=(16, 6), pady=(0, 6))

            body_label = ctk.CTkLabel(
                section_frame,
                text="",
                font=self.body_font,
                text_color="#3A3F4B",
                justify="left",
                anchor="w",
            )
            body_label.grid(row=1, column=1, sticky="nwe", padx=(14, 4))

            self.section_frames.append(section_frame)
            self.section_widgets[config["key"]] = {
                "title": title_label,
                "body": body_label,
                "icon_frame": icon_frame,
                "icon_label": icon_label,
                "icon_image": icon_image,
                "frame": section_frame,
            }

    def build_footer(self):
        self.button_container = ctk.CTkFrame(self.main, fg_color="transparent")
        self.button_container.grid(row=2, column=0, sticky="ew", padx=24, pady=(12, 30))
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
        content = self.language_content.get(self.language, self.language_content["EN"])
        self.title_label.configure(text=content["title"])
        self.return_button.configure(text=content["return_button"])

        sections = content["sections"]
        for config in self.section_configs:
            data = sections.get(config["key"], {})
            title_text = data.get("title", "")
            body_lines = data.get("body", [])
            bullet = "\u2022"  # •
            body_text = "\n".join(f"{bullet} {line.strip()}" for line in body_lines)

            widget = self.section_widgets.get(config["key"])
            if widget:
                widget["title"].configure(text=title_text)
                widget["body"].configure(text=body_text)

        self.update_toggle_styles()

    def set_language(self, language):
        if language == self.language:
            return
        if language not in self.LANGUAGE_ORDER:
            return
        self.language = language
        self.update_language()

    def update_toggle_styles(self):
        for lang, button in self.toggle_buttons.items():
            if lang == self.language:
                button.configure(
                    fg_color="transparent",
                    text_color="#005DFF",
                )
            else:
                button.configure(
                    fg_color="transparent",
                    text_color="#7A7A7A",
                )

    def on_resize(self, event):
        if event.widget is not self.parent:
            return
        if self.resize_job:
            self.parent.after_cancel(self.resize_job)
        self.resize_job = self.parent.after(self.RESIZE_DELAY, self.apply_responsive)

    def apply_responsive(self):
        width = max(self.parent.winfo_width(), 1)
        height = max(self.parent.winfo_height(), 1)

        width_ratio = width / self.BASE_DIMENSIONS[0]
        height_ratio = height / self.BASE_DIMENSIONS[1]
        scale = min(width_ratio, height_ratio)
        if height_ratio <= 1.0:
            scale *= 0.96
        if height_ratio <= 0.75:
            scale *= 0.92
        if height_ratio <= 0.62:
            scale *= 0.9
        scale = max(self.SCALE_LIMITS[0], min(self.SCALE_LIMITS[1], scale))

        padding_condense = 1.0
        if height_ratio <= 0.8:
            padding_condense *= 0.92
        if height_ratio <= 0.68:
            padding_condense *= 0.88
        if height_ratio <= 0.58:
            padding_condense *= 0.9
        padding_condense = max(0.6, padding_condense)

        button_condense = 1.0
        if height_ratio <= 0.8:
            button_condense *= 0.9
        if height_ratio <= 0.68:
            button_condense *= 0.88
        if height_ratio <= 0.58:
            button_condense *= 0.9
        button_condense = max(0.58, button_condense)

        icon_condense = 1.0
        if height_ratio <= 0.68:
            icon_condense *= 0.9
        if height_ratio <= 0.58:
            icon_condense *= 0.9

        tk_scaling_raw = self.parent.tk.call("tk", "scaling")
        try:
            widget_scaling = float(tk_scaling_raw)
        except (TypeError, ValueError):
            widget_scaling = 1.0
        if widget_scaling <= 0:
            widget_scaling = 1.0

        self.title_font.configure(
            size=int(max(16, self.BASE_FONT_SIZES["title"] * scale))
        )
        self.section_title_font.configure(
            size=int(max(9, self.BASE_FONT_SIZES["section_title"] * scale))
        )
        self.body_font.configure(
            size=int(max(6, self.BASE_FONT_SIZES["body"] * scale))
        )
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

        header_padx = int(
            max(12, min(80, self.HEADER_HORIZONTAL_PAD_BASE * (0.6 + scale)))
        )
        header_top = int(
            max(5, min(48, self.HEADER_TOP_PAD_BASE * (0.6 + scale) * padding_condense))
        )
        header_bottom = int(
            max(4, min(32, self.HEADER_BOTTOM_PAD_BASE * (0.6 + scale) * padding_condense))
        )
        self.header_frame.grid_configure(
            padx=header_padx, pady=(header_top, header_bottom)
        )

        toggle_pad_y = int(max(1, int(6 * scale * padding_condense)))
        self.toggle_container.grid_configure(pady=(toggle_pad_y, toggle_pad_y))
        toggle_width = int(max(38, min(150, self.TOGGLE_WIDTH_BASE * scale)))
        toggle_height = int(
            max(20, min(56, self.TOGGLE_HEIGHT_BASE * scale * button_condense))
        )
        for button in self.toggle_buttons.values():
            button.configure(width=toggle_width, height=toggle_height)

        usable_width = max(240, width - 24)
        target_card_width = int(self.CARD_BASE_WIDTH * scale)
        target_card_width = max(self.CARD_MIN_WIDTH, target_card_width)
        target_card_width = min(
            target_card_width, self.CARD_MAX_WIDTH, int(usable_width)
        )
        card_padx = max(12, (width - target_card_width) // 2)
        self.card_container.grid_configure(padx=card_padx)

        card_width = max(200, width - (card_padx * 2))
        pad_scale = 0.45 + min(scale, 1.1) * 0.7
        card_inner_pad = int(
            max(
                12,
                min(68, self.CARD_PADDING_BASE * pad_scale * padding_condense),
            )
        )
        section_top_base = self.SECTION_TOP_PAD_BASE * (0.45 + (scale * 0.85))
        section_bottom_base = self.SECTION_BOTTOM_PAD_BASE * (0.5 + (scale * 0.75))
        section_top = int(max(3, min(22, section_top_base * padding_condense)))
        section_bottom = int(max(6, min(26, section_bottom_base * padding_condense)))

        extra_last_pad = int(max(2, 8 * scale * padding_condense))
        for idx, frame in enumerate(self.section_frames):
            bottom = section_bottom
            if idx == len(self.section_frames) - 1:
                bottom = max(4, min(30, bottom + extra_last_pad))
            frame.grid_configure(padx=card_inner_pad, pady=(section_top, bottom))

        min_icon = max(8, int(self.ICON_MIN_SIZE * icon_condense))
        icon_size = int(
            max(
                min_icon,
                min(
                    self.ICON_MAX_SIZE,
                    self.ICON_BASE_SIZE * scale * icon_condense,
                ),
            )
        )
        for widget in self.section_widgets.values():
            widget["icon_frame"].configure(width=icon_size, height=icon_size)
            icon_image = widget.get("icon_image")
            if icon_image:
                icon_image.configure(size=(icon_size, icon_size))
            else:
                widget["icon_label"].configure(font=self.icon_font)

        self._update_section_wraps(
            card_width=card_width,
            card_pad=card_inner_pad,
            widget_scaling=widget_scaling,
        )

        button_pad_factor = 0.6 + (min(scale, 1.2) * 0.8)
        button_top = int(
            max(6, min(40, self.BUTTON_TOP_PAD_BASE * button_pad_factor * button_condense))
        )
        button_bottom = int(
            max(8, min(54, self.BUTTON_BOTTOM_PAD_BASE * button_pad_factor * button_condense))
        )
        self.button_container.grid_configure(
            padx=header_padx, pady=(button_top, button_bottom)
        )
        button_height = int(max(26, min(78, 52 * scale * button_condense)))
        button_width = int(max(148, min(340, 240 * scale)))
        self.return_button.configure(
            height=button_height,
            width=button_width,
        )

        self._resize_job = None

    def _update_section_wraps(self, *, card_width, card_pad, widget_scaling):
        if not self.section_widgets:
            return

        self.instructions_card.update_idletasks()
        card_width = max(card_width, self.instructions_card.winfo_width())

        scaling = max(widget_scaling, 0.1)
        min_wrap_base = max(140, int(card_width * 0.45))
        max_wrap_base = max(300, int(card_width * 1.04))
        body_pad_left = 16
        body_pad_right = 5

        for widget in self.section_widgets.values():
            section_frame = widget["frame"]
            section_frame.update_idletasks()

            icon_frame = widget["icon_frame"]
            icon_frame.update_idletasks()
            icon_width = icon_frame.winfo_width() or self.ICON_BASE_SIZE

            cell_bbox = section_frame.grid_bbox(1, 1)
            if cell_bbox:
                body_cell_width = cell_bbox[2]
            else:
                fallback_width = card_width - (card_pad * 1.5) - icon_width
                body_cell_width = max(150, fallback_width)

            available_px = body_cell_width - (body_pad_left + body_pad_right)
            if not cell_bbox:
                available_px -= 8
            available_px = max(100, available_px)

            target_px = max(min_wrap_base, min(max_wrap_base, available_px))
            wrap_px = min(target_px, available_px)

            wrap_units = max(36, int(round(wrap_px / scaling)))
            widget["body"].configure(wraplength=wrap_units)

    def return_to_menu(self):
        if self.on_return_callback:
            self.on_return_callback()

    def load_svg_image(self, svg_path, scale=1.0):
        try:
            svg_photo = TkSvgImage(file=str(svg_path), scale=scale)
            pil_image = ImageTk.getimage(svg_photo).convert("RGBA")
            return pil_image
        except (FileNotFoundError, ValueError) as error:
            print(f"Error loading SVG image '{svg_path}': {error}")
            return None

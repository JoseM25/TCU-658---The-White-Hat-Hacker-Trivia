import os
import customtkinter as ctk
from PIL import ImageTk
from tksvg import SvgImage as TkSvgImage


class InstructionsScreen:
    BASE_DIMENSIONS = (1280, 720)
    BASE_FONT_SIZES = {
        "title": 48,
        "section_title": 24,
        "body": 16,
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

    ICON_BASE_SIZE = 50
    ICON_MIN_SIZE = 28
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

        self.section_configs = [
            {"key": "objective", "icon_text": "OBJ", "color": "#005DFF"},
            {"key": "how_to_play", "icon_text": "PLAY", "color": "#0CA9A5"},
            {"key": "scoring", "icon_text": "PTS", "color": "#FF8C00"},
        ]

        self.language_content = {
            "EN": {
                "title": "How to Play",
                "return_button": "Main Menu",
                "sections": {
                    "objective": {
                        "title": "Objective",
                        "body": [
                            "Students identify and match ethical hacking definitions with the correct vocabulary terms.",
                            "Each definition uses supporting visuals or audio clips to reinforce learning.",
                            "Teachers can introduce new vocabulary items to keep the content up to date.",
                        ],
                    },
                    "how_to_play": {
                        "title": "How to Play",
                        "body": [
                            "A definition appears along with blank spaces representing the answer letter count.",
                            "Use the virtual keyboard to pick letters, helpers to reveal clues, or skip when needed.",
                            "Keep an eye on the timer and total score bar to track your ongoing performance.",
                        ],
                    },
                    "scoring": {
                        "title": "Scoring",
                        "body": [
                            "Correct answers award points and increase your total; wrong answers can be retried.",
                            "Faster answers grant higher scores and unlock available helpers like freezes or reveals.",
                            "A final summary highlights total score, accuracy, and the achieved mastery level.",
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
                            "El estudiantado identifica y empareja definiciones de hacking ético con los términos correctos.",
                            "Cada definición puede apoyarse en imágenes o clips de audio para facilitar la comprensión.",
                            "El personal docente puede añadir vocabulario nuevo para mantener el banco de términos.",
                        ],
                    },
                    "how_to_play": {
                        "title": "Cómo Jugar",
                        "body": [
                            "Aparece una definición junto con espacios en blanco que indican la cantidad de letras.",
                            "Usa el teclado virtual para seleccionar letras, comodines para obtener pistas o saltar si es necesario.",
                            "Observa el temporizador y la barra de puntaje para seguir tu rendimiento en tiempo real.",
                        ],
                    },
                    "scoring": {
                        "title": "Puntaje",
                        "body": [
                            "Las respuestas correctas suman puntos y aumentan el total; los errores pueden intentarse de nuevo.",
                            "Responder con rapidez concede más puntaje y habilita comodines como congelamientos o revelaciones.",
                            "Un resumen final muestra el puntaje total, la precisión y el nivel de dominio alcanzado.",
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
            family="Poppins Medium", size=self.BASE_FONT_SIZES["toggle"]
        )
        self.icon_font = ctk.CTkFont(
            family="Poppins Bold", size=self.BASE_FONT_SIZES["icon"], weight="bold"
        )

        self.logo_svg_path = os.path.join("recursos", "imagenes", "Hat.svg")

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
            fg_color="#FFFFFF",
            border_color="#D3DBEA",
            border_width=1,
            corner_radius=18,
        )
        self.toggle_container.grid(row=0, column=2, sticky="ne", padx=(12, 0))
        for idx, lang in enumerate(self.LANGUAGE_ORDER):
            button = ctk.CTkButton(
                self.toggle_container,
                text=lang,
                font=self.toggle_font,
                width=self.TOGGLE_WIDTH_BASE,
                height=self.TOGGLE_HEIGHT_BASE,
                corner_radius=14,
                fg_color="#FFFFFF",
                hover_color="#E4EBF8",
                text_color="#202632",
                command=lambda value=lang: self.set_language(value),
                border_width=0,
            )
            button.grid(
                row=0, column=idx, sticky="nsew", padx=(0 if idx == 0 else 1, 0), pady=4
            )
            self.toggle_container.grid_columnconfigure(idx, weight=1)
            self.toggle_buttons[lang] = button

    def build_card(self):
        self.card_container = ctk.CTkFrame(self.main, fg_color="transparent")
        self.card_container.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 12))
        self.card_container.grid_columnconfigure(0, weight=1)
        self.card_container.grid_rowconfigure(0, weight=1)

        self.instructions_card = ctk.CTkFrame(
            self.card_container,
            fg_color="#FFFFFF",
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

            icon_frame = ctk.CTkFrame(
                section_frame,
                fg_color=config["color"],
                corner_radius=18,
                width=self.ICON_BASE_SIZE,
                height=self.ICON_BASE_SIZE,
            )
            icon_frame.grid(row=0, column=0, rowspan=2, sticky="nw")
            icon_frame.grid_propagate(False)

            icon_label = ctk.CTkLabel(
                icon_frame,
                text=config["icon_text"],
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
            body_label.grid(row=1, column=1, sticky="nw", padx=(16, 6))

            self.section_frames.append(section_frame)
            self.section_widgets[config["key"]] = {
                "title": title_label,
                "body": body_label,
                "icon_frame": icon_frame,
                "icon_label": icon_label,
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
            body_text = "\n".join(f"- {line}" for line in body_lines)

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
                    fg_color="#005DFF",
                    text_color="#FFFFFF",
                    hover_color="#0044CC",
                )
            else:
                button.configure(
                    fg_color="#FFFFFF",
                    text_color="#202632",
                    hover_color="#E4EBF8",
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

        scale = min(width / self.BASE_DIMENSIONS[0], height / self.BASE_DIMENSIONS[1])
        scale = max(self.SCALE_LIMITS[0], min(self.SCALE_LIMITS[1], scale))

        self.title_font.configure(
            size=int(max(18, self.BASE_FONT_SIZES["title"] * scale))
        )
        self.section_title_font.configure(
            size=int(max(12, self.BASE_FONT_SIZES["section_title"] * scale))
        )
        self.body_font.configure(
            size=int(max(10, self.BASE_FONT_SIZES["body"] * scale))
        )
        self.button_font.configure(
            size=int(max(12, self.BASE_FONT_SIZES["button"] * scale))
        )
        self.toggle_font.configure(
            size=int(max(10, self.BASE_FONT_SIZES["toggle"] * scale))
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
        header_top = int(max(10, min(60, self.HEADER_TOP_PAD_BASE * (0.6 + scale))))
        header_bottom = int(
            max(8, min(40, self.HEADER_BOTTOM_PAD_BASE * (0.6 + scale)))
        )
        self.header_frame.grid_configure(
            padx=header_padx, pady=(header_top, header_bottom)
        )

        toggle_pad_y = int(max(2, 6 * scale))
        self.toggle_container.grid_configure(pady=(toggle_pad_y, toggle_pad_y))
        toggle_width = int(max(40, min(160, self.TOGGLE_WIDTH_BASE * scale)))
        toggle_height = int(max(24, min(60, self.TOGGLE_HEIGHT_BASE * scale)))
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
        card_inner_pad = int(
            max(
                16,
                min(80, self.CARD_PADDING_BASE * (0.6 + min(scale, 1.2))),
            )
        )
        section_top = int(max(6, min(32, self.SECTION_TOP_PAD_BASE * (0.8 + scale))))
        section_bottom = int(
            max(10, min(40, self.SECTION_BOTTOM_PAD_BASE * (0.8 + scale)))
        )

        for idx, frame in enumerate(self.section_frames):
            bottom = section_bottom
            if idx == len(self.section_frames) - 1:
                bottom += int(max(4, 10 * scale))
            frame.grid_configure(padx=card_inner_pad, pady=(section_top, bottom))

        icon_size = int(
            max(
                self.ICON_MIN_SIZE,
                min(self.ICON_MAX_SIZE, self.ICON_BASE_SIZE * scale),
            )
        )
        for widget in self.section_widgets.values():
            widget["icon_frame"].configure(width=icon_size, height=icon_size)
            widget["icon_label"].configure(font=self.icon_font)
            widget["body"].configure(
                wraplength=max(240, card_width - (icon_size + card_inner_pad + 90))
            )

        button_top = int(max(12, min(60, self.BUTTON_TOP_PAD_BASE * (0.8 + scale))))
        button_bottom = int(
            max(18, min(80, self.BUTTON_BOTTOM_PAD_BASE * (0.8 + scale)))
        )
        self.button_container.grid_configure(
            padx=header_padx, pady=(button_top, button_bottom)
        )
        self.return_button.configure(
            height=int(max(36, min(86, 52 * scale))),
            width=int(max(160, min(360, 240 * scale))),
        )

        self._resize_job = None

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

from tkinter import messagebox

import customtkinter as ctk
from PIL import Image, ImageTk
from tksvg import SvgImage as TkSvgImage

from juego.rutas_app import get_resource_images_dir


class MenuScreen:

    BASE_DIMENSIONS = (1280, 720)
    BASE_FONT_SIZES = {"title": 48, "button": 24}
    BASE_LOGO_SIZE = 150
    LOGO_MIN_SIZE = 64
    LOGO_MAX_SIZE = 220
    SCALE_LIMITS = (0.50, 1.60)
    RESIZE_DELAY = 80

    FOOTER_MIN_SIZE = (25, 20)
    FOOTER_MAX_SIZE = (200, 100)

    SVG_RASTER_SCALE = 2.0

    def __init__(self, parent, app_controller=None):
        self.parent = parent
        self.app_controller = app_controller
        self.menu_buttons = []
        self.logo_label = None
        self.title_label = None
        self.logo_image = None

        self.footer_items = []

        self.title_font = ctk.CTkFont(
            family="Poppins ExtraBold",
            size=self.BASE_FONT_SIZES["title"],
            weight="bold",
        )

        self.button_font = ctk.CTkFont(
            family="Poppins SemiBold", size=self.BASE_FONT_SIZES["button"]
        )

        self.images_dir = get_resource_images_dir()
        self.logo_svg_path = self.images_dir / "Hat.svg"

        self._resize_job = None

        self.build_ui()

        self.parent.bind("<Configure>", self.on_resize)
        self.apply_responsive()

    def build_ui(self):
        self.parent.grid_rowconfigure(0, weight=1)
        self.parent.grid_columnconfigure(0, weight=1)

        self.main = ctk.CTkFrame(self.parent, fg_color="transparent")
        self.main.grid(row=0, column=0, sticky="nsew")

        self.main.grid_rowconfigure(0, weight=0)
        self.main.grid_rowconfigure(1, weight=0)
        self.main.grid_rowconfigure(2, weight=1)
        self.main.grid_rowconfigure(3, weight=0)
        self.main.grid_columnconfigure(0, weight=1)

        self.logo_section()
        self.title_section()
        self.buttons_section()
        self.footer_section()

        self.apply_responsive()

    def logo_section(self):
        logo_container = ctk.CTkFrame(self.main, fg_color="transparent")
        logo_container.grid(row=0, column=0, sticky="n", pady=(0, 6))
        logo_container.grid_columnconfigure(0, weight=1)

        img = self.load_svg_image(self.logo_svg_path, scale=self.SVG_RASTER_SCALE)
        if img:
            self.logo_image = ctk.CTkImage(
                light_image=img,
                dark_image=img,
                size=(self.BASE_LOGO_SIZE, self.BASE_LOGO_SIZE),
            )
            self.logo_label = ctk.CTkLabel(
                logo_container, image=self.logo_image, text=""
            )
            self.logo_label.grid(row=0, column=0, sticky="n")

        else:
            ctk.CTkLabel(
                logo_container,
                text="(logo)",
                font=ctk.CTkFont(size=18),
                text_color="red",
            ).grid(row=0, column=0)

    def title_section(self):
        title_container = ctk.CTkFrame(self.main, fg_color="transparent")
        title_container.grid(row=1, column=0, sticky="n", pady=(2, 32))
        title_container.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(
            title_container,
            text="White Hat Hacker Trivia",
            font=self.title_font,
            text_color="#202632",
            anchor="center",
        )
        self.title_label.grid(row=0, column=0, pady=0, sticky="n")

    def buttons_section(self):

        button_configs = [
            ("Play", "#005DFF", "#003BB8", "start_game"),
            ("Instructions", "#00CFC5", "#009B94", "show_instructions"),
            ("Manage Questions", "#FFC553", "#CC9A42", "manage_questions"),
            ("Credits", "#FF8C00", "#CC6F00", "show_credits"),
            ("Exit", "#FF4F60", "#CC3F4D", "exit_game"),
        ]
        outer = ctk.CTkFrame(self.main, fg_color="transparent")
        outer.grid(row=2, column=0, sticky="nsew", pady=(0, 16))

        for c in range(3):
            outer.grid_columnconfigure(c, weight=1, uniform="buttons")
        outer.grid_rowconfigure(0, weight=1)

        inner_frame = ctk.CTkFrame(outer, fg_color="transparent")
        inner_frame.grid(row=0, column=1, sticky="nsew")
        inner_frame.grid_columnconfigure(0, weight=1)

        for row, (text, color, hover_color, method_name) in enumerate(button_configs):
            button = ctk.CTkButton(
                inner_frame,
                text=text,
                font=self.button_font,
                fg_color=color,
                hover_color=hover_color,
                command=getattr(self, method_name),
            )
            button.grid(row=row, column=0, sticky="ew", pady=8)
            self.menu_buttons.append(button)
            inner_frame.grid_rowconfigure(row, weight=1)

    def footer_section(self):
        footer_container = ctk.CTkFrame(self.main, fg_color="transparent")
        footer_container.grid(row=3, column=0, sticky="nsew", padx=0, pady=(12, 0))
        footer_container.grid_columnconfigure(0, weight=1)
        footer_container.grid_rowconfigure(0, weight=1)

        footer = ctk.CTkFrame(
            footer_container, fg_color="#D1D8E0", height=100, corner_radius=0
        )
        footer.grid(row=0, column=0, sticky="nsew", pady=0)
        footer.grid_propagate(False)

        for c in range(3):
            footer.grid_columnconfigure(c, weight=1)
        footer.grid_rowconfigure(0, weight=1)

        footer_images = [
            ("UCRLogo.png", (120, 60), "w", 50, "UCR"),
            ("ELMLogo.png", (140, 30), "", 10, "ELM"),
            ("TCULogo.png", (30, 60), "e", 50, "TCU"),
        ]

        self.footer_items.clear()

        for col, (filename, base_size, sticky, padx, fallback) in enumerate(
            footer_images
        ):
            path = self.images_dir / filename
            img = self.load_png_image(path)

            if img:
                image = ctk.CTkImage(
                    light_image=img,
                    dark_image=img,
                    size=base_size,
                )
                label = ctk.CTkLabel(footer, image=image, text="")
                label.grid(row=0, column=col, padx=padx, pady=10, sticky=sticky)
                self.footer_items.append({"image": image, "base_size": base_size})
            else:
                label = ctk.CTkLabel(footer, text=fallback, text_color="red")
                label.grid(row=0, column=col, padx=10, pady=10, sticky=sticky)
                self.footer_items.append({"image": None, "base_size": base_size})

    def on_resize(self, event):
        if event.widget is not self.parent:
            return

        if self._resize_job:
            self.parent.after_cancel(self._resize_job)
        self._resize_job = self.parent.after(self.RESIZE_DELAY, self.apply_responsive)

    def apply_responsive(self):
        w = max(self.parent.winfo_width(), 1)
        h = max(self.parent.winfo_height(), 1)

        scale = min(w / self.BASE_DIMENSIONS[0], h / self.BASE_DIMENSIONS[1])
        scale = max(self.SCALE_LIMITS[0], min(self.SCALE_LIMITS[1], scale))

        self.title_font.configure(
            size=int(max(16, self.BASE_FONT_SIZES["title"] * scale))
        )
        self.button_font.configure(
            size=int(max(12, self.BASE_FONT_SIZES["button"] * scale))
        )

        pad_y = int(max(4, min(12, 10 * scale)))
        height = int(max(24, 48 * scale))
        for button in self.menu_buttons:
            button.grid_configure(pady=pad_y)
            button.configure(height=height)

        if self.logo_image is not None:
            desired = int(
                max(
                    self.LOGO_MIN_SIZE,
                    min(self.LOGO_MAX_SIZE, self.BASE_LOGO_SIZE * scale),
                )
            )
            self.logo_image.configure(size=(desired, desired))

        footer_scale = min(scale, 1.2)

        for item in self.footer_items:
            img = item["image"]
            w, h = item["base_size"]

            new_width = int(
                max(
                    self.FOOTER_MIN_SIZE[0],
                    min(self.FOOTER_MAX_SIZE[0], w * footer_scale),
                )
            )
            new_height = int(
                max(
                    self.FOOTER_MIN_SIZE[1],
                    min(self.FOOTER_MAX_SIZE[1], h * footer_scale),
                )
            )
            img.configure(size=(new_width, new_height))

        self._resize_job = None

    def load_svg_image(self, svg_path, scale=1.0):
        try:
            svg_photo = TkSvgImage(file=str(svg_path), scale=scale)
            pil = ImageTk.getimage(svg_photo).convert("RGBA")
            return pil
        except (FileNotFoundError, ValueError) as e:
            print(f"Error loading SVG image '{svg_path}': {e}")
            return None

    def load_png_image(self, png_path):
        try:
            with Image.open(png_path) as img:
                return img.convert("RGBA").copy()
        except (FileNotFoundError, OSError) as e:
            print(f"Error loading PNG image '{png_path}': {e}")
            return None

    def start_game(self):
        if self.app_controller:
            self.app_controller.start_game()
        else:
            print("Iniciando juego...")
            messagebox.showinfo(
                "Juego Iniciado", "Aquí va la lógica para iniciar el juego."
            )

    def show_instructions(self):
        if self.app_controller:
            self.app_controller.show_instructions()
        else:
            messagebox.showinfo(
                "Instrucciones", "Aquí van las instrucciones del juego."
            )

    def manage_questions(self):
        if self.app_controller:
            self.app_controller.show_manage_questions()
        else:
            messagebox.showinfo(
                "Manage Questions", "Manage questions screen coming soon."
            )

    def show_credits(self):
        if self.app_controller:
            self.app_controller.show_credits()
        else:
            messagebox.showinfo("Créditos", "Aquí van los créditos del juego.")

    def exit_game(self):
        result = messagebox.askyesno("Salir", "¿Estás seguro que quieres salir?")
        if result:
            self.parent.destroy()

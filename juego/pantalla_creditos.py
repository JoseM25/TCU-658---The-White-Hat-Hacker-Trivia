import tkinter

import customtkinter as ctk
from PIL import ImageTk
from tksvg import SvgImage as TkSvgImage

from juego.ayudantes_responsivos import get_dpi_scaling, get_logical_dimensions
from juego.rutas_app import get_resource_images_dir


class CreditsScreen:
    BASE_DIMENSIONS = (1280, 720)
    BASE_FONT_SIZES = {"title": 48, "body": 16, "button": 24}
    BASE_LOGO_SIZE = 100
    LOGO_MIN_SIZE = 50
    LOGO_MAX_SIZE = 150
    SCALE_LIMITS = (0.35, 1.60)
    RESIZE_DELAY = 80
    SVG_RASTER_SCALE = 2.0
    BUTTON_TOP_PAD_BASE = 10
    BUTTON_BOTTOM_PAD_BASE = 30
    BUTTON_EXTRA_BOTTOM_PAD = 24

    def __init__(self, parent, on_return_callback):
        self.parent = parent
        self.on_return_callback = on_return_callback
        self.logo_label = None
        self.title_label = None
        self.divider_container = None
        self.divider_bar = None
        self.body_container = None
        self.body_label = None
        self.button_container = None
        self.return_button = None
        self.logo_image = None

        self.title_font = ctk.CTkFont(
            family="Poppins ExtraBold",
            size=self.BASE_FONT_SIZES["title"],
            weight="bold",
        )

        self.body_font = ctk.CTkFont(
            family="Open Sans Regular", size=self.BASE_FONT_SIZES["body"], weight="bold"
        )

        self.button_font = ctk.CTkFont(
            family="Poppins SemiBold", size=self.BASE_FONT_SIZES["button"]
        )

        self.logo_svg_path = get_resource_images_dir() / "Hat.svg"
        self.resize_job = None

        self.build_ui()
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
        self.main.grid_rowconfigure(1, weight=0)
        self.main.grid_rowconfigure(2, weight=0)
        self.main.grid_rowconfigure(3, weight=1)
        self.main.grid_rowconfigure(4, weight=0)
        self.main.grid_columnconfigure(0, weight=1)

        self.logo_section()
        self.title_section()
        self.divider_section()
        self.body_section()
        self.button_section()

    def logo_section(self):
        logo_container = ctk.CTkFrame(self.main, fg_color="transparent")
        logo_container.grid(row=0, column=0, sticky="n", pady=(20, 10))
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
            self.logo_label = ctk.CTkLabel(
                logo_container,
                text="(logo)",
                font=ctk.CTkFont(size=18),
                text_color="red",
            )
            self.logo_label.grid(row=0, column=0)

    def title_section(self):
        title_container = ctk.CTkFrame(self.main, fg_color="transparent")
        title_container.grid(row=1, column=0, sticky="n", pady=(0, 20))
        title_container.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(
            title_container,
            text="Credits",
            font=self.title_font,
            text_color="#202632",
            anchor="center",
        )
        self.title_label.grid(row=0, column=0, pady=0, sticky="n")

    def divider_section(self):
        self.divider_container = ctk.CTkFrame(self.main, fg_color="transparent")
        self.divider_container.grid(row=2, column=0, sticky="ew", pady=(0, 24), padx=16)
        self.divider_container.grid_columnconfigure(0, weight=1)

        self.divider_bar = ctk.CTkFrame(
            self.divider_container, height=8, fg_color="#005DFF"
        )
        self.divider_bar.grid(row=0, column=0, sticky="ew")

    def body_section(self):
        self.body_container = ctk.CTkFrame(self.main, fg_color="transparent")
        self.body_container.grid(row=3, column=0, sticky="nsew", pady=(0, 10), padx=20)
        self.body_container.grid_columnconfigure(0, weight=1)
        self.body_container.grid_rowconfigure(0, weight=1)

        text_frame = ctk.CTkFrame(self.body_container, fg_color="transparent")
        text_frame.grid(row=0, column=0, sticky="nsew")
        text_frame.grid_columnconfigure(0, weight=1)
        text_frame.grid_rowconfigure(0, weight=1)

        credits_text = """
            Application developed by Computer Science Student Jose Antonio Mora Monge in 2025 for TCU 658: 
            "Cooperación con el Proceso de Enseñanza-Aprendizaje del Inglés en Educación Secundaria Pública"
            from the School of Modern Languages at the University of Costa Rica (UCR).


            
            Carried out under the guidance of Professor Daniela María Barrantes Torres, Coordinator of TCU-658
            and Professor at the School of Modern Languages at UCR.

            
            
            All resources used follow Public Domain License
        """

        self.body_label = ctk.CTkLabel(
            text_frame,
            text=credits_text.strip(),
            font=self.body_font,
            text_color="#404040",
            anchor="center",
            justify="center",
            wraplength=600,
        )
        self.body_label.grid(row=0, column=0, pady=5, padx=10, sticky="nsew")

    def button_section(self):
        self.button_container = ctk.CTkFrame(self.main, fg_color="transparent")
        self.button_container.grid(row=4, column=0, sticky="ew", pady=(10, 30))
        self.button_container.grid_columnconfigure(0, weight=1)

        self.return_button = ctk.CTkButton(
            self.button_container,
            text="Main Menu",
            font=self.button_font,
            fg_color="#005DFF",
            hover_color="#003BB8",
            command=self.return_to_menu,
            width=200,
            height=50,
        )
        self.return_button.grid(row=0, column=0, pady=0)

    def on_resize(self, event):
        if event.widget is not self.parent:
            return

        if self.resize_job:
            self.parent.after_cancel(self.resize_job)
        self.resize_job = self.parent.after(self.RESIZE_DELAY, self.apply_responsive)

    def apply_responsive(self):
        w, h = get_logical_dimensions(self.parent, self.BASE_DIMENSIONS)

        # grid_configure() no pasa por el escalado de CTk, necesitamos escalar manualmente
        dpi = get_dpi_scaling(self.body_container)

        scale = min(w / self.BASE_DIMENSIONS[0], h / self.BASE_DIMENSIONS[1])
        scale = max(self.SCALE_LIMITS[0], min(self.SCALE_LIMITS[1], scale))

        self.title_font.configure(
            size=int(max(16, self.BASE_FONT_SIZES["title"] * scale))
        )
        self.body_font.configure(size=int(max(9, self.BASE_FONT_SIZES["body"] * scale)))
        self.button_font.configure(
            size=int(max(12, self.BASE_FONT_SIZES["button"] * scale))
        )

        if self.logo_image:
            desired = int(
                max(
                    self.LOGO_MIN_SIZE,
                    min(self.LOGO_MAX_SIZE, self.BASE_LOGO_SIZE * scale),
                )
            )
            self.logo_image.configure(size=(desired, desired))

        min_gutter = 12
        capacity_w = max(100, w - 2 * min_gutter)

        divider_base = 900
        divider_target = int(divider_base * scale)
        divider_soft_cap = min(int(w * 0.92), 1100)
        divider_w = max(320, min(capacity_w, divider_soft_cap, divider_target))
        divider_padx = max(min_gutter, (w - divider_w) // 2)
        self.divider_container.grid_configure(padx=int(divider_padx * dpi))

        body_base = 1100
        body_target = int(body_base * scale)
        body_soft_cap = min(int(w * 0.92), 1600)
        body_w = max(520, min(capacity_w, body_soft_cap, max(body_target, divider_w)))
        body_padx = max(min_gutter, (w - body_w) // 2)
        self.body_container.grid_configure(padx=int(body_padx * dpi))

        if self.divider_bar:
            self.divider_bar.configure(height=int(max(3, min(10, 8 * scale))))

        self.return_button.configure(
            height=int(max(30, 50 * scale)),
            width=int(max(150, 200 * scale)),
        )

        top_pad = int(max(6, self.BUTTON_TOP_PAD_BASE * scale))
        bottom_pad = (
            int(max(12, self.BUTTON_BOTTOM_PAD_BASE * scale))
            + self.BUTTON_EXTRA_BOTTOM_PAD
        )
        self.button_container.grid_configure(
            pady=(int(top_pad * dpi), int(bottom_pad * dpi))
        )

        if self.body_label:
            self.body_label.configure(wraplength=max(260, body_w - 40))

        self.resize_job = None

    def load_svg_image(self, svg_path, scale=1.0):
        try:
            svg_photo = TkSvgImage(file=str(svg_path), scale=scale)
            pil = ImageTk.getimage(svg_photo).convert("RGBA")
            return pil
        except (FileNotFoundError, ValueError) as e:
            print(f"Error loading SVG image '{svg_path}': {e}")
            return None

    def cleanup(self):
        try:
            self.parent.unbind("<Configure>")
        except tkinter.TclError:
            pass
        if self.resize_job:
            try:
                self.parent.after_cancel(self.resize_job)
            except tkinter.TclError:
                pass
            self.resize_job = None

    def return_to_menu(self):
        self.cleanup()
        if self.on_return_callback:
            self.on_return_callback()

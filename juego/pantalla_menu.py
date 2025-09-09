import os
from tkinter import messagebox, TclError
import customtkinter as ctk
from PIL import ImageTk
from tksvg import SvgImage as TkSvgImage


class MenuScreen:
    # Constantes
    BASE_DIMENSIONS = (1280, 720)
    BASE_FONT_SIZES = {"title": 48, "button": 24}
    BASE_LOGO_SIZE = 150
    SCALE_LIMITS = (0.50, 1.60)
    RESIZE_DELAY = 80

    def __init__(self, parent):
        self.parent = parent
        self.menu_buttons = []
        self.logo_label = None
        self.title_label = None

        # Image cache
        self._image_cache = {}
        self._current_logo_size = 0
        self._resize_job = None

        # Crear Fuentes
        self.title_font = ctk.CTkFont(
            family="Poppins ExtraBold",
            size=self.BASE_FONT_SIZES["title"],
            weight="bold",
        )

        self.button_font = ctk.CTkFont(
            family="Poppins SemiBold", size=self.BASE_FONT_SIZES["button"]
        )

        self.logo_svg_path = os.path.join("recursos", "imagenes", "Hat.svg")

        self.parent.bind("<Configure>", self.on_resize)
        self.build_ui()

    def load_svg_image(self, svg_path, size):
        cache_key = f"{svg_path}_{size}"
        if cache_key in self._image_cache:
            return self._image_cache[cache_key]

        try:
            # Cargar SVG y convertir a PNG
            photo = TkSvgImage(file=svg_path, scale=1.0)
            # Crear Imagen PIL
            pil = ImageTk.getimage(photo).convert("RGBA")
            img = ctk.CTkImage(light_image=pil, dark_image=pil, size=(size, size))
            self._image_cache[cache_key] = img
            return img
        except (FileNotFoundError, TclError, ValueError) as e:
            print(f"Error loading SVG image: {e}")
            return None

    def load_footer_image(self, path, size):
        cache_key = f"{path}_{size[0]}_{size[1]}"
        if cache_key in self._image_cache:
            return self._image_cache[cache_key]

        try:
            pil = ImageTk.Image.open(path).convert("RGBA")
            img = ctk.CTkImage(light_image=pil, dark_image=pil, size=size)
            self._image_cache[cache_key] = img
            return img
        except (FileNotFoundError, OSError) as e:
            print(f"Error loading footer image: {e}")
            return None

    def build_ui(self):
        self.parent.grid_rowconfigure(0, weight=1)
        self.parent.grid_columnconfigure(0, weight=1)

        self.main = ctk.CTkFrame(self.parent, fg_color="transparent")
        self.main.grid(row=0, column=0, sticky="nsew")

        self.main.grid_rowconfigure(0, weight=0)  # Logo
        self.main.grid_rowconfigure(1, weight=0)  # Titulo
        self.main.grid_rowconfigure(2, weight=1)  # Botones
        self.main.grid_rowconfigure(3, weight=0)  # Footer
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

        img = self.load_svg_image(self.logo_svg_path, self.BASE_LOGO_SIZE)
        if img:
            self.logo_label = ctk.CTkLabel(logo_container, image=img, text="")
            self.logo_label.grid(row=0, column=0, sticky="n")
            self._current_logo_size = self.BASE_LOGO_SIZE

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
        # Configuracion botones
        button_configs = [
            ("Play", "#005DFF", "#003BB8", "start_game"),
            ("Instructions", "#00CFC5", "#009B94", "show_instructions"),
            ("Manage Questions", "#FFC553", "#CC9A42", "manage_questions"),
            ("Credits", "#FF8C00", "#CC6F00", "show_credits"),
            ("Exit", "#FF4F60", "#CC3F4D", "exit_game"),
        ]
        outer = ctk.CTkFrame(self.main, fg_color="transparent")
        outer.grid(row=2, column=0, sticky="nsew", pady=(0, 16))

        # Configurar columnas con tamano uniforme
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

        # Configuracion logos Footer
        footer_images = [
            ("UCRLogo.png", (120, 60)),
            ("ELMLogo.png", (140, 30)),
            ("TCULogo.png", (30, 60)),
        ]

        fallback_texts = ["UCR", "ELM", "TCU"]
        positions = ["w", "", "e"]
        paddings = [50, 10, 50]

        for col, ((filename, size), fallback) in enumerate(
            zip(footer_images, fallback_texts)
        ):
            path = os.path.join("recursos", "imagenes", filename)
            img = self.load_footer_image(path, size)
            sticky = positions[col]
            padx = paddings[col]

            if img:
                label = ctk.CTkLabel(footer, image=img, text="")
                label.image = img
                label.grid(row=0, column=col, padx=padx, pady=10, sticky=sticky)
            else:
                ctk.CTkLabel(
                    footer,
                    text=fallback,
                    text_color="#666666",
                ).grid(row=0, column=col, padx=10, pady=10)

    def on_resize(self, event):
        if event.widget is not self.parent:
            return

        if self._resize_job is not None:
            self.parent.after_cancel(self._resize_job)
        self._resize_job = self.parent.after(self.RESIZE_DELAY, self.apply_responsive)

    def apply_responsive(self):
        w = max(self.parent.winfo_width(), 1)
        h = max(self.parent.winfo_height(), 1)

        # Calcular factor de escala
        scale = min(w / self.BASE_DIMENSIONS[0], h / self.BASE_DIMENSIONS[1])
        scale = max(self.SCALE_LIMITS[0], min(self.SCALE_LIMITS[1], scale))

        self.title_font.configure(
            size=int(max(16, self.BASE_FONT_SIZES["title"] * scale))
        )
        self.button_font.configure(
            size=int(max(12, self.BASE_FONT_SIZES["button"] * scale))
        )

        # Actualizar botones
        pad_y = int(max(4, min(12, 10 * scale)))

        for button in self.menu_buttons:
            button.grid_configure(pady=pad_y)
            button.configure(height=int(max(24, 48 * scale)))

        # Actualizar Logo si tamano cambia mucho
        desired_logo_size = int(max(64, min(200, self.BASE_LOGO_SIZE * scale)))
        if abs(desired_logo_size - self._current_logo_size) > 10 and self.logo_label:
            img = self.load_svg_image(self.logo_svg_path, desired_logo_size)
            if img:
                self.logo_label.configure(image=img)
                self._current_logo_size = desired_logo_size
        self._resize_job = None

    def start_game(self):
        print("Iniciando juego...")
        messagebox.showinfo(
            "Juego Iniciado", "Aquí va la lógica para iniciar el juego."
        )

    def show_instructions(self):
        messagebox.showinfo("Instrucciones", "Aquí van las instrucciones del juego.")

    def manage_questions(self):
        messagebox.showinfo(
            "Manejo de Preguntas", "Aquí va la sección para manejar preguntas."
        )

    def show_credits(self):
        messagebox.showinfo("Créditos", "Aquí van los créditos del juego.")

    def exit_game(self):
        result = messagebox.askyesno("Salir", "¿Estás seguro que quieres salir?")
        if result:
            self.parent.quit()

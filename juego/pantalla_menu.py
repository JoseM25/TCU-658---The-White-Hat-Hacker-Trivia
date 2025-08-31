import os
from tkinter import messagebox, TclError
import customtkinter as ctk
from PIL import ImageTk
from tksvg import SvgImage as TkSvgImage


class MenuScreen:
    def __init__(self, parent):
        self.parent = parent
        self.menu_buttons = []
        self.logo_label = None
        self.title_label = None
        self.inner_frame = None

        # Crear Fuentes
        self.title_font = ctk.CTkFont(
            family="Poppins ExtraBold", size=48, weight="bold"
        )

        self.button_font = ctk.CTkFont(family="Poppins SemiBold", size=24)

        self.logo_svg_path = os.path.join("recursos", "imagenes", "Hat.svg")

        self.base_w, self.base_h = 1280, 720
        self.base_title_px, self.base_btn_px = 48, 24
        self.base_logo_px = 150
        self._current_logo_px = 0
        self._resize_job = None

        self.parent.bind("<Configure>", self._on_resize)

        self.build_ui()

    def load_svg_image(self, svg_path, size=150):
        try:
            # Cargar SVG y convertir a PNG
            photo = TkSvgImage(file=svg_path, scale=1.0)
            # Crear Imagen PIL
            pil = ImageTk.getimage(photo).convert("RGBA")

            return ctk.CTkImage(light_image=pil, dark_image=pil, size=(size, size))
        except (FileNotFoundError, TclError, ValueError) as e:
            print(f"Error loading SVG image: {e}")
            return None

    def build_ui(self):
        self.parent.grid_rowconfigure(0, weight=1)
        self.parent.grid_columnconfigure(0, weight=1)

        self.main = ctk.CTkFrame(self.parent, fg_color="transparent")
        self.main.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)

        self.main.grid_rowconfigure(0, weight=0)  # Logo
        self.main.grid_rowconfigure(1, weight=0)  # Titulo
        self.main.grid_rowconfigure(2, weight=1)  # Botones
        self.main.grid_rowconfigure(3, weight=0)  # Footer
        self.main.grid_columnconfigure(0, weight=1)

        self.logo_section()
        self.title_section()
        self.buttons_section()
        self.footer_section()

        self._apply_responsive()

    def logo_section(self):
        logo_container = ctk.CTkFrame(self.main, fg_color="transparent")
        logo_container.grid(row=0, column=0, sticky="n", pady=(0, 6))
        logo_container.grid_columnconfigure(0, weight=1)

        img = self.load_svg_image(self.logo_svg_path, size=150)
        if img:
            self.logo_label = ctk.CTkLabel(logo_container, image=img, text="")
            self.logo_label.image = img
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
        outer = ctk.CTkFrame(self.main, fg_color="transparent")
        outer.grid(row=2, column=0, sticky="nsew", pady=(0, 16))
        for c in (0, 1, 2):
            outer.grid_columnconfigure(c, weight=1)
        outer.grid_rowconfigure(0, weight=1)

        self.inner_frame = ctk.CTkFrame(outer, fg_color="transparent")
        self.inner_frame.grid(row=0, column=1, sticky="nsew")
        self.inner_frame.grid_columnconfigure(0, weight=1)

        def add_buttons(row, text, color, hover_color, cmd):
            button = ctk.CTkButton(
                self.inner_frame,
                text=text,
                font=self.button_font,
                fg_color=color,
                hover_color=hover_color,
                command=cmd,
            )
            button.grid(row=row, column=0, sticky="ew", padx=0, pady=(8, 8))
            self.menu_buttons.append(button)

        add_buttons(0, "Play", "#005DFF", "#003BB8", self.start_game)
        add_buttons(1, "Instructions", "#00CFC5", "#009B94", self.show_instructions)
        add_buttons(2, "Manage Questions", "#FFC553", "#CC9A42", self.manage_questions)
        add_buttons(3, "Credits", "#FF8C00", "#CC6F00", self.show_credits)
        add_buttons(4, "Exit", "#FF4F60", "#CC3F4D", self.exit_game)

        for row in range(5):
            self.inner_frame.grid_rowconfigure(row, weight=1)

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

    def _on_resize(self, event):
        if event.widget is self.parent:
            if self._resize_job:
                self.parent.after_cancel(self._resize_job)
            self._resize_job = self.parent.after(80, self._apply_responsive)

    def _apply_responsive(self):
        w = max(self.parent.winfo_width(), 1)
        h = max(self.parent.winfo_height(), 1)

        s = min(w / self.base_w, h / self.base_h)
        s = max(0.50, min(1.60, s))

        self.title_font.configure(size=int(max(16, self.base_title_px * s)))
        self.button_font.configure(size=int(max(12, self.base_btn_px * s)))

        pad_y = int(max(4, min(12, 10 * s)))

        if w > 1200:
            button_padx = int(w * 0.15)
        elif w > 800:
            button_padx = int(w * 0.00000001)
        else:
            button_padx = 0

        if hasattr(self, "inner_frame"):
            self.inner_frame.grid_configure(padx=button_padx)

        for b in getattr(self, "menu_buttons", []):
            b.grid_configure(pady=(pad_y, pad_y))
            b.configure(height=int(48 * s))

        desired_logo = int(max(64, min(200, self.base_logo_px * s)))
        if desired_logo != self._current_logo_px and hasattr(self, "logo_label"):
            img = self.load_svg_image(self.logo_svg_path, size=desired_logo)
            if img:
                self.logo_label.configure(image=img)
                self.logo_label.image = img
                self._current_logo_px = desired_logo

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

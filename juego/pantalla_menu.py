import os
from tkinter import messagebox, TclError
import customtkinter as ctk
from PIL import ImageTk
from tksvg import SvgImage as TkSvgImage


class MenuScreen:
    def __init__(self, parent):
        self.parent = parent

        # Tamanos base para escalar
        self.base_width = 1280
        self.base_height = 720
        self.min_scale = 0.85
        self.max_scale = 1.35

        self._resize_job = None
        self.current_logo_px = 0
        self.menu_buttons = []

        # Crear Fuentes

        self.title_font = ctk.CTkFont(
            family="Poppins ExtraBold", size=48, weight="bold"
        )

        self.button_font = ctk.CTkFont(family="Poppins SemiBold", size=24)

        self.logo_svg_path = os.path.join("recursos", "imagenes", "Hat.svg")

        self.setup_menu()

        # Recalcular al redimensionar
        self.parent.bind("<Configure>", self._on_window_resize)

    def load_svg_image(self, svg_path, width=200, height=200):
        try:
            # Cargar SVG y convertir a PNG
            photo = TkSvgImage(file=svg_path, scale=1.0)
            # Crear Imagen PIL
            pil = ImageTk.getimage(photo).convert("RGBA")

            # Convertir Imagen a CTKImage
            ctk_image = ctk.CTkImage(
                light_image=pil, dark_image=pil, size=(width, height)
            )

            return ctk_image
        except (FileNotFoundError, TclError, ValueError) as e:
            print(f"Error loading SVG image: {e}")
            return None

    def setup_menu(self):
        # Limpiar Widgets Existentes
        for widget in self.parent.winfo_children():
            widget.destroy()

        self.parent.grid_rowconfigure(0, weight=1)
        self.parent.grid_columnconfigure(0, weight=1)

        # Frame Contenedor Principal
        self.main_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        # Configurar grid
        self.main_frame.grid_rowconfigure(0, weight=1)  # Logo
        self.main_frame.grid_rowconfigure(1, weight=0)  # Titulo
        self.main_frame.grid_rowconfigure(2, weight=4)  # Botones
        self.main_frame.grid_rowconfigure(3, weight=1)  # Pie de Pagina
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Logo
        self.create_logo()

        # Titulo
        self.create_title()

        # Botones Menu
        self.create_menu_buttons()

        # Pie de Pagina
        self.create_footer()

        # Escalado Inicial
        self._apply_responsive()

    def create_logo(self):
        # Frame Logo
        logo_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        logo_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        logo_frame.grid_columnconfigure(0, weight=1)

        # Cargar Imagen SVG
        svg_path = os.path.join("recursos", "imagenes", "Hat.svg")
        logo_image = self.load_svg_image(svg_path, width=150, height=150)

        if logo_image:
            # Crear label con Imagen
            self.logo_label = ctk.CTkLabel(
                logo_frame,
                image=logo_image,
                text="",  # Sin texto
            )
            self.logo_label.image = logo_image
            self.logo_label.grid(row=0, column=0)
        else:
            # Manejar error al cargar imagen
            self.logo_label = ctk.CTkLabel(
                logo_frame,
                text="Error loading logo",
                font=ctk.CTkFont(size=24),
                text_color="red",
            )
            self.logo_label.grid(row=0, column=0)

    def create_title(self):
        # Frame titulo
        title_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        title_frame.grid(row=1, column=0, sticky="ew", pady=(0, 30))
        title_frame.grid_columnconfigure(0, weight=1)

        # Titulo Principal
        self.title_label = ctk.CTkLabel(
            title_frame,
            text="White Hat Hacker Trivia",
            font=self.title_font,
            text_color="#202632",
        )
        self.title_label.grid(row=0, column=0, pady=10)

    def create_menu_buttons(self):
        # Frame Botones (3 columnas para centrar un panel interno)
        self.buttons_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.buttons_frame.grid(row=2, column=0, sticky="nsew")
        for c in (0, 1, 2):
            self.buttons_frame.grid_columnconfigure(c, weight=1)
        self.buttons_frame.grid_rowconfigure(0, weight=1)

        # Frame interno con ancho máximo controlado
        self.buttons_inner = ctk.CTkFrame(self.buttons_frame, fg_color="transparent")
        self.buttons_inner.grid(row=0, column=1, sticky="n", padx=0)
        self.buttons_inner.grid_columnconfigure(0, weight=1)

        def add_btn(row, text, color, cmd):
            b = ctk.CTkButton(
                self.buttons_inner,
                text=text,
                font=self.button_font,
                fg_color=color,
                hover_color="#000000",
                command=cmd,
            )
            b.grid(row=row, column=0, sticky="ew", pady=10)
            self.menu_buttons.append(b)

        add_btn(0, "Play", "#005DFF", self.start_game)
        add_btn(1, "Instructions", "#00CFC5", self.show_instructions)
        add_btn(2, "Manage Questions", "#FFC553", self.manage_questions)
        add_btn(3, "Credits", "#FF8C00", self.show_credits)
        add_btn(4, "Exit", "#FF4F60", self.exit_game)

        for r in range(5):
            self.buttons_inner.grid_rowconfigure(r, weight=1, uniform="buttons")

    def create_footer(self):
        # Frame Pie de Pagina
        footer_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        footer_frame.grid(row=3, column=0, sticky="ew", pady=(30, 0))
        footer_frame.grid_columnconfigure(0, weight=1)

    def _apply_responsive(self):
        w = max(self.parent.winfo_width(), 1)
        h = max(self.parent.winfo_height(), 1)

        s = min(w / self.base_width, h / self.base_height)
        s = max(self.min_scale, min(self.max_scale, s))

        # Typography: named fonts propagate to widgets automatically
        self.title_font.configure(size=int(max(24, min(72, 48 * s))))
        self.button_font.configure(size=int(max(14, min(36, 24 * s))))

        # Panel width cap (fluid but bounded)
        panel_w = int(min(max(320, 0.45 * w), 680))
        self.buttons_inner.configure(width=panel_w)
        self.buttons_inner.grid_propagate(False)  # keep a tidy column look

        # Harmonized button height (optional; comment out to let height be natural)
        btn_h = int(max(48, min(96, 64 * s)))
        for r in range(len(self.menu_buttons)):
            self.buttons_inner.grid_rowconfigure(r, minsize=btn_h)
        for btn in self.menu_buttons:
            btn.configure(width=panel_w, height=btn_h)

        # Logo: only re-render if pixel target changed
        desired_px = int(max(80, min(220, 150 * s)))
        if desired_px != self.current_logo_px:
            img = self.load_svg_image(self.logo_svg_path, desired_px, desired_px)
            if img:
                self.logo_label.configure(image=img)
                self.logo_label.image = img
                self.current_logo_px = desired_px

    def _on_window_resize(self, event):
        if event.widget is self.parent:
            if self._resize_job:
                self.parent.after_cancel(self._resize_job)
            self._resize_job = self.parent.after(80, self._apply_responsive)

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

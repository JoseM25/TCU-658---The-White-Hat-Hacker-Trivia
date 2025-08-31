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
        self.base_logo_size = 150
        self.current_scale = 1.0
        self._current_logo_px = self.base_logo_size
        self.menu_buttons = []

        # Crear Fuentes
        self.title_font_path = os.path.join(
            "recursos", "fuentes", "Poppins-ExtraBold.ttf"
        )
        self.button_font_path = os.path.join(
            "recursos", "fuentes", "Poppins-SemiBold.ttf"
        )
        self.title_font = ctk.CTkFont(
            family=self.title_font_path, size=48, weight="bold"
        )
        self.button_font = ctk.CTkFont(family=self.button_font_path, size=24)

        self.setup_menu()

        # Recalcular al redimensionar
        self.parent.bind("<Configure>", self.on_window_resize)

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

    def _apply_global_scaling(self):
        # Calcular radios
        w = max(self.parent.winfo_width(), 1)
        h = max(self.parent.winfo_height(), 1)
        scale_w = w / self.base_width
        scale_h = h / self.base_height
        new_scale = max(0.75, min(1.5, scale_w, scale_h))

        # Solo calcular cuando es necesario
        if abs(new_scale - self.current_scale) >= 0.05:
            ctk.set_widget_scaling(new_scale)
            self.current_scale = new_scale

        # Actualizar logo
        desired_logo_px = max(
            80, min(int(self.base_logo_size * self.current_scale), 250)
        )
        if desired_logo_px != self._current_logo_px and hasattr(self, "logo_label"):
            svg_path = os.path.join("recursos", "imagenes", "Hat.svg")
            logo_image = self.load_svg_image(
                svg_path, width=desired_logo_px, height=desired_logo_px
            )
            if logo_image:
                self.logo_label.configure(image=logo_image)
                self.logo_label.image = logo_image
                self._current_logo_px = desired_logo_px

    def on_window_resize(self, event):
        if event.widget == self.parent:
            self._apply_global_scaling()

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
        self.main_frame.grid_rowconfigure(2, weight=2)  # Botones
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
        self._apply_global_scaling()

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
            self.logo_label.grid(row=0, column=0)
            self.logo_label.image = logo_image
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
        # Frame Botones
        buttons_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        buttons_frame.grid(row=2, column=0, sticky="nsew")
        buttons_frame.grid_columnconfigure(0, weight=1)

        # Agregar Path Fuente Botones
        button_font_path = os.path.join("recursos", "fuentes", "Poppins-SemiBold.ttf")
        button_font = ctk.CTkFont(family=button_font_path, size=24)

        # Boton Jugar
        start_button = ctk.CTkButton(
            buttons_frame,
            text="Play",
            font=self.button_font,
            fg_color="#005DFF",
            hover_color="#000000",
            command=self.start_game,
        )
        start_button.grid(row=0, column=0, pady=10, padx=40, sticky="ew")
        self.menu_buttons.append(start_button)

        # Boton Instrucciones
        instructions_button = ctk.CTkButton(
            buttons_frame,
            text="Instructions",
            font=self.button_font,
            fg_color="#00CFC5",
            hover_color="#000000",
            command=self.show_instructions,
        )
        instructions_button.grid(row=1, column=0, pady=10, padx=40, sticky="ew")
        self.menu_buttons.append(instructions_button)

        # Boton Manejar Preguntas
        questions_button = ctk.CTkButton(
            buttons_frame,
            text="Manage Questions",
            font=self.button_font,
            fg_color="#FFC553",
            hover_color="#000000",
            command=self.manage_questions,
        )
        questions_button.grid(row=2, column=0, pady=10, padx=40, sticky="ew")
        self.menu_buttons.append(questions_button)

        # Boton Creditos
        credits_button = ctk.CTkButton(
            buttons_frame,
            text="Credits",
            font=self.button_font,
            fg_color="#FF8C00",
            hover_color="#000000",
            command=self.show_credits,
        )
        credits_button.grid(row=3, column=0, pady=10, padx=40, sticky="ew")
        self.menu_buttons.append(credits_button)

        # Boton Salir
        exit_button = ctk.CTkButton(
            buttons_frame,
            text="Exit",
            font=button_font,
            fg_color="#FF4F60",
            hover_color="#000000",
            command=self.exit_game,
        )
        exit_button.grid(row=4, column=0, pady=10, padx=40, sticky="ew")
        self.menu_buttons.append(exit_button)

    def create_footer(self):
        # Frame Pie de Pagina
        footer_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        footer_frame.grid(row=3, column=0, sticky="ew", pady=(30, 0))
        footer_frame.grid_columnconfigure(0, weight=1)

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

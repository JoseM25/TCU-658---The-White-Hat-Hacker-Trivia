import os
from tkinter import messagebox
import customtkinter as ctk
from PIL import ImageTk
from tksvg import SvgImage as TkSvgImage


class MenuScreen:
    def __init__(self, parent):
        self.parent = parent
        self.setup_menu()

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
        except Exception as e:
            print(f"Error loading SVG image: {e}")
            return None

    def setup_menu(self):
        # Limpiar Widgets Existentes
        for widget in self.parent.winfo_children():
            widget.destroy()

        # Frame Contenedor Principal
        self.main_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Logo
        self.create_logo()

        # Titulo
        self.create_title()

        # Botones Menu
        self.create_menu_buttons()

        # Pie de Pagina
        self.create_footer()

    def create_logo(self):
        # Frame Logo
        logo_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        logo_frame.pack(pady=(0, 30))

        # Cargar Imagen SVG
        svg_path = os.path.join("recursos", "imagenes", "Hat.svg")
        logo_image = self.load_svg_image(svg_path, width=150, height=150)

        if logo_image:
            # Crear label con Imagen
            logo_label = ctk.CTkLabel(
                logo_frame,
                image=logo_image,
                text="",  # Sin texto
            )
            logo_label.pack()
        else:
            # Manejar error al cargar imagen
            error_label = ctk.CTkLabel(
                logo_frame,
                text="Error loading logo",
                font=ctk.CTkFont(size=80),
                text_color="red",
            )
            error_label.pack()

    def create_title(self):
        # Frame titulo
        title_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        title_frame.pack(pady=(0, 50))

        # Agregar Path Fuente Titulo
        font_path = os.path.join("recursos", "fuentes", "Poppins-ExtraBold.ttf")

        # Titulo Principal
        title_label = ctk.CTkLabel(
            title_frame,
            text="White Hat Hacker Trivia",
            font=ctk.CTkFont(family=font_path, size=48, weight="bold"),
            text_color="#202632",
        )
        title_label.pack(pady=10)

    def create_menu_buttons(self):
        # Frame Botones
        buttons_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        buttons_frame.pack(expand=True)

        # Agregar Path Fuente Botones
        button_font_path = os.path.join("recursos", "fuentes", "Poppins-SemiBold.ttf")

        # Configuracion Estilo Botones
        button_width = 300
        button_height = 50
        button_font = ctk.CTkFont(family=button_font_path, size=24)

        # Boton Jugar
        start_button = ctk.CTkButton(
            buttons_frame,
            text="Play",
            width=button_width,
            height=button_height,
            font=button_font,
            fg_color="#005DFF",
            hover_color="#000000",
            command=self.start_game,
        )
        start_button.pack(pady=15)

        # Boton Instrucciones
        instructions_button = ctk.CTkButton(
            buttons_frame,
            text="Instructions",
            width=button_width,
            height=button_height,
            font=button_font,
            fg_color="#00CFC5",
            hover_color="#000000",
            command=self.show_instructions,
        )
        instructions_button.pack(pady=15)

        # Boton Manejar Preguntas
        questions_button = ctk.CTkButton(
            buttons_frame,
            text="Manage Questions",
            width=button_width,
            height=button_height,
            font=button_font,
            fg_color="#FFC553",
            hover_color="#000000",
            command=self.manage_questions,
        )
        questions_button.pack(pady=15)

        # Boton Creditos
        credits_button = ctk.CTkButton(
            buttons_frame,
            text="Credits",
            width=button_width,
            height=button_height,
            font=button_font,
            fg_color="#FF8C00",
            hover_color="#000000",
            command=self.show_credits,
        )
        credits_button.pack(pady=15)

        # Boton Salir
        exit_button = ctk.CTkButton(
            buttons_frame,
            text="Exit",
            width=button_width,
            height=button_height,
            font=button_font,
            fg_color="#FF4F60",
            hover_color="#000000",
            command=self.exit_game,
        )
        exit_button.pack(pady=15)

    def create_footer(self):
        # Frame Pie de Pagina
        footer_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        footer_frame.pack(side="bottom", pady=(50, 0))

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

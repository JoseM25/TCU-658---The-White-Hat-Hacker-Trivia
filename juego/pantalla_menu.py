import os
from tkinter import messagebox
import customtkinter as ctk


class MenuScreen:
    def __init__(self, parent):
        self.parent = parent
        self.setup_menu()

    def setup_menu(self):
        # Limpiar Widgets Existentes
        for widget in self.parent.winfo_children():
            widget.destroy()

        # Frame Contenedor Principal
        self.main_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Titulo
        self.create_title()

        # Botones Menu
        self.create_menu_buttons()

        # Pie de Pagina
        self.create_footer()

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

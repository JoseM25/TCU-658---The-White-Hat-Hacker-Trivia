import os
from tkinter import messagebox, TclError
import customtkinter as ctk
from PIL import ImageTk
from tksvg import SvgImage as TkSvgImage


class MenuScreen:
    def __init__(self, parent):
        self.parent = parent
        self.menu_buttons = []

        # Crear Fuentes
        self.title_font = ctk.CTkFont(
            family="Poppins ExtraBold", size=48, weight="bold"
        )

        self.button_font = ctk.CTkFont(family="Poppins SemiBold", size=24)

        self.logo_svg_path = os.path.join("recursos", "imagenes", "Hat.svg")

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
        self.main.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        self.main.grid_rowconfigure(0, weight=1)
        self.main.grid_rowconfigure(1, weight=0)
        self.main.grid_rowconfigure(2, weight=6)
        self.main.grid_rowconfigure(3, weight=1)
        self.main.grid_columnconfigure(0, weight=1)

        self.logo_section()
        self.title_section()
        self.buttons_section()
        self.footer_section()

    def logo_section(self):
        logo_container = ctk.CTkFrame(self.main, fg_color="transparent")
        logo_container.grid(row=0, column=0, sticky="n", pady=(0, 20))
        logo_container.grid_columnconfigure(0, weight=1)

        img = self.load_svg_image(self.logo_svg_path, size=150)
        if img:
            logo_img = ctk.CTkLabel(logo_container, image=img, text="")
            logo_img.image = img
            logo_img.grid(row=0, column=0, sticky="n")
        else:
            ctk.CTkLabel(
                logo_container,
                text="(logo)",
                font=ctk.CTkFont(size=18),
                text_color="red",
            ).grid(row=0, column=0)

    def title_section(self):
        title_container = ctk.CTkFrame(self.main, fg_color="transparent")
        title_container.grid(row=1, column=0, sticky="n", pady=(0, 30))
        title_container.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            title_container,
            text="White Hat Hacker Trivia",
            font=self.title_font,
            text_color="#202632",
            anchor="center",
        ).grid(row=0, column=0, pady=10, sticky="n")

    def buttons_section(self):
        outer = ctk.CTkFrame(self.main, fg_color="transparent")
        outer.grid(row=2, column=0, sticky="nsew")
        outer.grid_columnconfigure(0, weight=1)
        outer.grid_columnconfigure(1, weight=2)
        outer.grid_columnconfigure(2, weight=1)
        outer.grid_rowconfigure(0, weight=1)

        inner = ctk.CTkFrame(outer, fg_color="transparent")
        inner.grid(row=0, column=1, sticky="nsew", padx=16)
        inner.grid_columnconfigure(0, weight=1)

        def add_buttons(row, text, color, cmd):
            button = ctk.CTkButton(
                inner,
                text=text,
                font=self.button_font,
                fg_color=color,
                hover_color="#000000",
                command=cmd,
            )
            button.grid(row=row, column=0, sticky="nsew", pady=10, ipady=6)
            self.menu_buttons.append(button)

        add_buttons(0, "Play", "#005DFF", self.start_game)
        add_buttons(1, "Instructions", "#00CFC5", self.show_instructions)
        add_buttons(2, "Manage Questions", "#FFC553", self.manage_questions)
        add_buttons(3, "Credits", "#FF8C00", self.show_credits)
        add_buttons(4, "Exit", "#FF4F60", self.exit_game)

        for row in range(5):
            inner.grid_rowconfigure(row, weight=1, uniform="buttons")

    def footer_section(self):
        footer_container = ctk.CTkFrame(self.main, fg_color="transparent")
        footer_container.grid(row=3, column=0, sticky="ew", pady=(30, 0))
        footer_container.grid_columnconfigure(0, weight=1)

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

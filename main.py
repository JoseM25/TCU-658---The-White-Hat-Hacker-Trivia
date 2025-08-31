import customtkinter as ctk
from juego.pantalla_menu import MenuScreen

ctk.set_appearance_mode("white")
ctk.set_default_color_theme("blue")

root = ctk.CTk()

root.title("White Hat Hacker Trivia!")

root.geometry("1280x720")

root.resizable(True, True)
root.minsize(400, 300)
root.maxsize(3840, 2160)

root.configure(fg_color="#F5F7FA")

menu = MenuScreen(root)

root.mainloop()

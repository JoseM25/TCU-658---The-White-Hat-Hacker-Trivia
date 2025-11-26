from juego.pantalla_menu import MenuScreen
from juego.pantalla_creditos import CreditsScreen
from juego.pantalla_instrucciones import InstructionsScreen
from juego.pantalla_preguntas import ManageQuestionsScreen
from juego.pantalla_juego import GameScreen


class AppController:
    def __init__(self, root):
        self.root = root
        self.current_screen = None
        self.show_menu()

    def show_menu(self):
        self.current_screen = MenuScreen(self.root, app_controller=self)

    def show_instructions(self):
        self.current_screen = InstructionsScreen(
            self.root, on_return_callback=self.show_menu
        )

    def show_credits(self):
        self.current_screen = CreditsScreen(
            self.root, on_return_callback=self.show_menu
        )

    def show_manage_questions(self):
        self.current_screen = ManageQuestionsScreen(
            self.root, on_return_callback=self.show_menu
        )

    def start_game(self):
        self.current_screen = GameScreen(self.root, on_return_callback=self.show_menu)

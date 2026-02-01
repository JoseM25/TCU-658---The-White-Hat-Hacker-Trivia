from juego.pantalla_creditos import CreditsScreen
from juego.pantalla_instrucciones import InstructionsScreen
from juego.pantalla_juego import GameScreen
from juego.pantalla_menu import MenuScreen
from juego.pantalla_preguntas import ManageQuestionsScreen


class AppController:
    def __init__(self, root, tts_service=None, sfx_service=None):
        self.root = root
        self.tts = tts_service
        self.sfx = sfx_service
        self.current_screen = None
        self.show_menu()

    def cleanup_current_screen(self):
        if self.current_screen and hasattr(self.current_screen, "cleanup"):
            try:
                self.current_screen.cleanup()
            except (AttributeError, RuntimeError, TypeError):
                pass

    def show_menu(self):
        self.cleanup_current_screen()
        self.current_screen = MenuScreen(self.root, app_controller=self)

    def show_instructions(self):
        self.cleanup_current_screen()
        self.current_screen = InstructionsScreen(
            self.root, on_return_callback=self.show_menu
        )

    def show_credits(self):
        self.cleanup_current_screen()
        self.current_screen = CreditsScreen(
            self.root, on_return_callback=self.show_menu
        )

    def show_manage_questions(self):
        self.cleanup_current_screen()
        self.current_screen = ManageQuestionsScreen(
            self.root, on_return_callback=self.show_menu, tts_service=self.tts
        )

    def start_game(self):
        self.cleanup_current_screen()
        self.current_screen = GameScreen(
            self.root,
            on_return_callback=self.show_menu,
            tts_service=self.tts,
            sfx_service=self.sfx,
        )

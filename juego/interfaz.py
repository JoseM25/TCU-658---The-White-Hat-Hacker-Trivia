from juego.pantalla_menu import MenuScreen
from juego.pantalla_creditos import CreditsScreen


class AppController:
    def __init__(self, root):
        self.root = root
        self.current_screen = None
        self.show_menu()

    def show_menu(self):
        self.current_screen = MenuScreen(self.root, app_controller=self)

    def show_credits(self):
        self.current_screen = CreditsScreen(
            self.root, on_return_callback=self.show_menu
        )

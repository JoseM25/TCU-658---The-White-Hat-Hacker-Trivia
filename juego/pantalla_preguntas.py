from juego.ayudantes_responsivos import (
    LayoutCalculator,
    ResponsiveScaler,
    SizeStateCalculator,
)
from juego.manejador_imagenes import ImageHandler
from juego.pantalla_preguntas_config import (
    SCREEN_BASE_DIMENSIONS,
    SCREEN_COLORS,
    SCREEN_DEFINITION_PADDING_PROFILE,
    SCREEN_DEFINITION_STACK_BREAKPOINT,
    SCREEN_DEFINITION_WRAP_FILL_PROFILE,
    SCREEN_DEFINITION_WRAP_LIMITS,
    SCREEN_DEFINITION_WRAP_PIXEL_PROFILE,
    SCREEN_DETAIL_WEIGHT,
    SCREEN_FONT_SPECS,
    SCREEN_GLOBAL_SCALE_FACTOR,
    SCREEN_HEADER_SIZE_MULTIPLIER,
    SCREEN_ICONS,
    SCREEN_LOW_RES_SCALE_PROFILE,
    SCREEN_RESIZE_DELAY,
    SCREEN_SCALE_LIMITS,
    SCREEN_SIDEBAR_WEIGHT,
    SCREEN_SIDEBAR_WIDTH_PROFILE,
    SCREEN_SIZES,
    SCREEN_VIEWPORT_WRAP_RATIO_PROFILE,
    QuestionRepository,
    ScreenFontRegistry,
)
from juego.pantalla_preguntas_manejadores import QuestionScreenHandlersMixin
from juego.rutas_app import (
    get_data_questions_path,
    get_data_root,
    get_resource_audio_dir,
    get_resource_images_dir,
    get_resource_root,
    get_user_images_dir,
)
from juego.servicio_tts import TTSService


class ManageQuestionsScreen(QuestionScreenHandlersMixin):

    # Constantes de configuración
    BASE_DIMENSIONS = SCREEN_BASE_DIMENSIONS
    SCALE_LIMITS = SCREEN_SCALE_LIMITS
    RESIZE_DELAY = SCREEN_RESIZE_DELAY
    GLOBAL_SCALE_FACTOR = SCREEN_GLOBAL_SCALE_FACTOR
    HEADER_SIZE_MULTIPLIER = SCREEN_HEADER_SIZE_MULTIPLIER
    SIDEBAR_WEIGHT = SCREEN_SIDEBAR_WEIGHT
    DETAIL_WEIGHT = SCREEN_DETAIL_WEIGHT

    ICONS = SCREEN_ICONS
    COLORS = SCREEN_COLORS
    SIZES = SCREEN_SIZES
    DEFINITION_PADDING_PROFILE = SCREEN_DEFINITION_PADDING_PROFILE
    DEFINITION_WRAP_FILL_PROFILE = SCREEN_DEFINITION_WRAP_FILL_PROFILE
    DEFINITION_WRAP_PIXEL_PROFILE = SCREEN_DEFINITION_WRAP_PIXEL_PROFILE
    DEFINITION_WRAP_LIMITS = SCREEN_DEFINITION_WRAP_LIMITS
    DEFINITION_STACK_BREAKPOINT = SCREEN_DEFINITION_STACK_BREAKPOINT
    VIEWPORT_WRAP_RATIO_PROFILE = SCREEN_VIEWPORT_WRAP_RATIO_PROFILE
    SIDEBAR_WIDTH_PROFILE = SCREEN_SIDEBAR_WIDTH_PROFILE
    LOW_RES_SCALE_PROFILE = SCREEN_LOW_RES_SCALE_PROFILE
    FONT_SPECS = SCREEN_FONT_SPECS

    QUESTIONS_FILE = get_data_questions_path()
    IMAGES_DIR = get_resource_images_dir()
    AUDIO_DIR = get_resource_audio_dir()

    def __init__(self, parent, on_return_callback=None, tts_service=None):
        super().__init__()
        self.parent = parent
        self.on_return_callback = on_return_callback

        self.init_fonts()
        self.init_scalers()
        self.init_services(tts_service)
        self.init_data()
        self.init_screen()

    def init_fonts(self):
        self.font_registry = ScreenFontRegistry(self.FONT_SPECS)
        self.font_registry.attach_attributes(self)
        self.font_base_sizes = dict(self.font_registry.base_sizes)
        self.font_min_sizes = dict(self.font_registry.min_sizes)

    def init_scalers(self):
        self.scaler = ResponsiveScaler(
            base_dimensions=self.BASE_DIMENSIONS,
            scale_limits=self.SCALE_LIMITS,
            global_scale_factor=self.GLOBAL_SCALE_FACTOR,
        )

        profiles = {
            "sidebar_width": self.SIDEBAR_WIDTH_PROFILE,
            "definition_padding": self.DEFINITION_PADDING_PROFILE,
            "wrap_fill": self.DEFINITION_WRAP_FILL_PROFILE,
        }

        self.size_calc = SizeStateCalculator(self.scaler, self.SIZES, profiles)
        self.layout_calc = LayoutCalculator(self.scaler, profiles)

    def init_services(self, tts_service):
        self.tts = tts_service or TTSService(self.AUDIO_DIR)
        data_root = get_data_root()
        self.image_handler = ImageHandler(
            self.IMAGES_DIR,
            user_images_dir=get_user_images_dir(),
            data_root=data_root,
            resource_root=get_resource_root(),
        )
        self.repository = QuestionRepository(self.QUESTIONS_FILE)

    def init_data(self):
        self.questions = list(self.repository.questions)
        self.filtered_questions = list(self.questions)
        self.current_modal = None
        self.current_question = (
            self.filtered_questions[0] if self.filtered_questions else None
        )

    def init_screen(self):
        # Inicializar estado desde el mixin de UI
        self.init_view_state()
        self.init_icons()
        self.init_scale_state()

        # Limpiar widgets existentes
        for widget in self.parent.winfo_children():
            widget.destroy()

        # Construir la interfaz
        self.build_ui()

        # Aplicar tamaño adaptable
        self.apply_responsive()

        # Configurar enlaces de eventos
        self.parent.bind("<Button-1>", self.handle_global_click, add="+")
        self.parent.bind("<Configure>", self.on_resize)

    def refresh_question_cache(self):
        self.questions[:] = list(self.repository.questions)

    def filter_questions(self, query):
        query = (query or "").strip().lower()
        filtered = (
            [q for q in self.questions if query in q.get("title", "").lower()]
            if query
            else list(self.questions)
        )
        self.filtered_questions[:] = filtered

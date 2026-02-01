import json
import tkinter as tk

import customtkinter as ctk

from juego.ayudantes_responsivos import ResponsiveScaler
from juego.comodines import WildcardManager
from juego.logica import ScoringSystem
from juego.manejador_imagenes import ImageHandler
from juego.pantalla_juego_config import (
    GAME_BASE_DIMENSIONS,
    GAME_BASE_SIZES,
    GAME_COLORS,
    GAME_FONT_SPECS,
    GAME_GLOBAL_SCALE_FACTOR,
    GAME_ICONS,
    GAME_PROFILES,
    GAME_RESIZE_DELAY,
    GAME_SCALE_LIMITS,
    KEYBOARD_LAYOUT,
    GameFontRegistry,
    GameSizeCalculator,
)
from juego.pantalla_juego_constructor_ui import GameUIBuilderMixin
from juego.pantalla_juego_iconos import GameIconsMixin
from juego.rutas_app import (
    get_data_questions_path,
    get_data_root,
    get_resource_audio_dir,
    get_resource_images_dir,
    get_resource_root,
    get_user_images_dir,
)
from juego.servicio_tts import TTSService


class GameScreenBase(GameIconsMixin, GameUIBuilderMixin):

    # Importar constantes de configuración
    BASE_DIMENSIONS = GAME_BASE_DIMENSIONS
    SCALE_LIMITS = GAME_SCALE_LIMITS
    RESIZE_DELAY = GAME_RESIZE_DELAY
    COLORS = GAME_COLORS
    ICONS = GAME_ICONS
    BASE_SIZES = GAME_BASE_SIZES
    KEYBOARD_LAYOUT = KEYBOARD_LAYOUT

    # Escala de renderizado SVG
    SVG_RASTER_SCALE = 2.0

    # Número máximo de preguntas a mantener en el historial
    MAX_QUESTION_HISTORY = 50

    # Declaraciones de atributos a nivel de clase (inicializados en métodos auxiliares de __init__)
    definition_scrollbar_visible: bool | None
    definition_scrollbar_manager: str | None
    definition_scroll_update_job: str | None
    timer_frozen_visually: bool
    double_points_visually_active: bool

    def __init__(
        self, parent, on_return_callback=None, tts_service=None, sfx_service=None
    ):
        self.parent = parent
        self.on_return_callback = on_return_callback
        self.sfx = sfx_service

        # Inicializar todos los atributos de estado
        self.init_game_state()
        self.init_ui_references()
        self.init_paths_and_services(tts_service)

        # Inicializar sistema responsivo
        self.init_responsive_system()

        # Cargar datos y construir UI
        self.load_questions()
        self.build_ui()

    def init_game_state(self):
        self.current_question = None
        self.questions = []
        self.available_questions = []
        self.score = 0
        self.current_answer = ""
        self.timer_seconds = 0
        self.audio_enabled = True
        if self.sfx and hasattr(self.sfx, "is_muted"):
            self.audio_enabled = not self.sfx.is_muted()
        self.timer_running = False
        self.timer_job = None
        self.timer_generation = 0  # Counter to invalidate stale timer callbacks
        self.questions_answered = 0
        self.game_completed = False
        self.scoring_system = None
        self.wildcard_manager = WildcardManager()
        self.question_timer = 0
        self.question_mistakes = 0

        # Manejo de redimensionamiento
        self.resize_job = None

        # Estado del flujo del juego
        self.processing_correct_answer = False
        self.awaiting_modal_decision = False
        self.stored_modal_data = None
        self.question_history = []
        self.viewing_history_index = -1

        # Manejo del teclado físico
        self.physical_key_pressed = None
        self.key_feedback_job = None
        self._keypress_bind_id = None
        self._keyrelease_bind_id = None

        # Seguimiento del estado visual
        self.timer_frozen_visually = False
        self.double_points_visually_active = False
        self.ultimo_tam_imagen = 0

    def init_ui_references(self):
        # Diseño principal
        self.main = None
        self.header_frame = None
        self.header_left_container = None
        self.header_center_container = None
        self.header_right_container = None

        # Componentes del encabezado
        self.back_button = None
        self.back_arrow_icon = None
        self.timer_container = None
        self.score_container = None
        self.audio_container = None
        self.timer_label = None
        self.timer_icon_label = None
        self.score_label = None
        self.star_icon_label = None
        self.multiplier_label = None
        self.audio_toggle_btn = None

        # Componentes del contenedor de pregunta
        self.question_container = None
        self.image_frame = None
        self.image_label = None
        self.definition_frame = None
        self.definition_scroll_wrapper = None
        self.definition_scroll = None
        self.def_inner = None
        self.definition_label = None
        self.definition_scrollbar_visible = None
        self.definition_scrollbar_manager = None
        self.definition_scroll_update_job = None
        self.answer_boxes_frame = None
        self.answer_box_labels = []

        # Componentes del teclado
        self.keyboard_frame = None
        self.keyboard_buttons = []
        self.delete_button = None
        self.key_button_map = {}

        # Botones de acción
        self.action_buttons_frame = None
        self.skip_button = None
        self.check_button = None

        # Referencias de imagen
        self.current_image = None

        # Referencias de iconos
        self.audio_icon_on = None
        self.audio_icon_off = None
        self.clock_icon = None
        self.star_icon = None
        self.delete_icon = None
        self.freeze_icon = None
        self.info_icon = None
        self.info_icon_label = None
        self.lightning_icon = None
        self.lightning_icon_label = None
        self.freeze_wildcard_icon = None

        # Componentes del panel de comodines
        self.wildcards_frame = None
        self.wildcard_x2_btn = None
        self.wildcard_hint_btn = None
        self.wildcard_freeze_btn = None
        self.charges_frame = None
        self.charges_label = None

        # Componentes de retroalimentación
        self.feedback_label = None
        self.feedback_animation_job = None

        # Referencias de modales
        self.completion_modal = None
        self.summary_modal = None
        self.skip_modal = None

        # Atributos de fuente (establecidos por font_registry.attach_attributes)
        self.timer_font = None
        self.score_font = None
        self.definition_font = None
        self.keyboard_font = None
        self.answer_box_font = None
        self.button_font = None
        self.header_button_font = None
        self.header_label_font = None
        self.feedback_font = None
        self.wildcard_font = None
        self.charges_font = None
        self.multiplier_font = None

    def init_paths_and_services(self, tts_service):
        resource_images_dir = get_resource_images_dir()
        resource_audio_dir = get_resource_audio_dir()
        data_root = get_data_root()
        resource_root = get_resource_root()

        self.images_dir = resource_images_dir
        self.audio_dir = resource_audio_dir
        self.questions_path = get_data_questions_path()

        # Manejador de imágenes para cargar iconos
        self.image_handler = ImageHandler(
            self.images_dir,
            user_images_dir=get_user_images_dir(),
            data_root=data_root,
            resource_root=resource_root,
        )

        # Servicio TTS
        self.tts = tts_service or TTSService(self.audio_dir)

    def init_responsive_system(self):
        # Crear escalador
        self.scaler = ResponsiveScaler(
            self.BASE_DIMENSIONS,
            self.SCALE_LIMITS,
            global_scale_factor=GAME_GLOBAL_SCALE_FACTOR,
        )

        # Crear calculador de tamaños
        self.size_calc = GameSizeCalculator(self.scaler, GAME_PROFILES)

        # Crear registro de fuentes y adjuntar fuentes como atributos
        self.font_registry = GameFontRegistry(GAME_FONT_SPECS)
        self.font_registry.attach_attributes(self)

        # Almacenar tamaños base y mínimos para escalado de fuentes
        self.font_base_sizes = self.font_registry.base_sizes
        self.font_min_sizes = self.font_registry.min_sizes

        # Seguimiento de estado
        self.current_scale = 1.0
        self.current_window_width = self.BASE_DIMENSIONS[0]
        self.current_window_height = self.BASE_DIMENSIONS[1]
        self.size_state = {}

        # Caché de iconos para redimensionamiento eficiente
        self.icon_cache = {}

    def get_window_scaling(self):
        root = self.parent.winfo_toplevel() if self.parent else None
        try:
            scaling = ctk.ScalingTracker.get_window_scaling(root) if root else 1.0
        except (AttributeError, KeyError):
            scaling = 1.0
        if not scaling or scaling <= 0:
            return 1.0
        return scaling

    def get_logical_dimensions(self):
        if not self.parent or not self.parent.winfo_exists():
            return self.BASE_DIMENSIONS
        scaling = self.get_window_scaling()
        width = max(int(round(self.parent.winfo_width() / scaling)), 1)
        height = max(int(round(self.parent.winfo_height() / scaling)), 1)
        return width, height

    def get_current_scale(self):
        w, h = self.get_logical_dimensions()
        low_res_profile = GAME_PROFILES.get("low_res")
        return self.scaler.calculate_scale(w, h, low_res_profile)

    def scale_value(self, base, scale, min_value=None, max_value=None):
        return self.scaler.scale_value(base, scale, min_value, max_value)

    def get_scaled_image_size(self, scale=None):
        if self.size_state and "image_size" in self.size_state:
            return self.size_state["image_size"]
        s = scale or self.get_current_scale()
        return self.scale_value(
            self.BASE_SIZES["image_base"],
            s,
            self.BASE_SIZES["image_min"],
            self.BASE_SIZES["image_max"],
        )

    def get_scaled_box_size(self, scale=None):
        if self.size_state and "answer_box" in self.size_state:
            return self.size_state["answer_box"]
        s = scale or self.get_current_scale()
        return self.scale_value(
            self.BASE_SIZES["answer_box_base"],
            s,
            self.BASE_SIZES["answer_box_min"],
            self.BASE_SIZES["answer_box_max"],
        )

    def load_questions(self):
        try:
            with open(self.questions_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.questions = data.get("questions", [])
                self.available_questions = list(self.questions)
                self.scoring_system = ScoringSystem(len(self.questions))
                self.wildcard_manager.reset_game()
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading questions: {e}")
            self.questions = []
            self.available_questions = []
            self.scoring_system = ScoringSystem(1)
            self.wildcard_manager.reset_game()

    # =========================================================================
    # Manejo de Barra de Desplazamiento de Definición
    # =========================================================================

    def set_definition_text(self, text):
        if self.definition_label and self.definition_label.winfo_exists():
            self.definition_label.configure(text=text)
        self.queue_definition_scroll_update()

    def queue_definition_scroll_update(self):
        if not self.parent or not self.parent.winfo_exists():
            return
        if self.definition_scroll_update_job:
            try:
                self.parent.after_cancel(self.definition_scroll_update_job)
            except tk.TclError:
                pass
            self.definition_scroll_update_job = None
        try:
            self.definition_scroll_update_job = self.parent.after_idle(
                self.update_definition_scrollbar_visibility
            )
        except tk.TclError:
            self.definition_scroll_update_job = None
            self.update_definition_scrollbar_visibility()

    def update_definition_scrollbar_visibility(self):
        self.definition_scroll_update_job = None
        if not self.definition_scroll or not self.definition_scroll.winfo_exists():
            return
        if (
            not self.definition_scroll_wrapper
            or not self.definition_scroll_wrapper.winfo_exists()
        ):
            return

        content = None
        if self.def_inner and self.def_inner.winfo_exists():
            content = self.def_inner
        elif self.definition_label and self.definition_label.winfo_exists():
            content = self.definition_label
        if not content:
            return

        try:
            content.update_idletasks()
            self.definition_scroll_wrapper.update_idletasks()
        except tk.TclError:
            return

        wrapper_height = self.definition_scroll_wrapper.winfo_height()
        if wrapper_height <= 1:
            wrapper_height = self.definition_scroll_wrapper.winfo_reqheight()
        content_height = content.winfo_reqheight()

        needs_scroll = content_height > (wrapper_height + 2)
        self.set_definition_scrollbar_visible(needs_scroll)

    def set_definition_scrollbar_visible(self, visible):
        if self.definition_scrollbar_visible is visible:
            return

        scrollbar = self.get_scrollbar_widget(self.definition_scroll)
        if not scrollbar or not scrollbar.winfo_exists():
            return

        manager = self.definition_scrollbar_manager or scrollbar.winfo_manager()
        if not manager:
            manager = "grid"
        self.definition_scrollbar_manager = manager

        if visible:
            if manager == "grid":
                scrollbar.grid()
            elif manager == "pack":
                scrollbar.pack()
            elif manager == "place":
                scrollbar.place()
        else:
            if manager == "grid":
                scrollbar.grid_remove()
            elif manager == "pack":
                scrollbar.pack_forget()
            elif manager == "place":
                scrollbar.place_forget()

        self.definition_scrollbar_visible = visible

    def get_scrollbar_widget(self, scrollable):
        if not scrollable:
            return None
        for attr in (
            "_scrollbar",
            "_scrollbar_vertical",
            "_y_scrollbar",
            "_scrollbar_y",
        ):
            scrollbar = getattr(scrollable, attr, None)
            if scrollbar:
                return scrollbar
        return None

    # =========================================================================
    # Manejo de Cajas de Respuesta
    # =========================================================================

    def create_answer_boxes(self, word_length):
        box_sz = self.get_scaled_box_size()
        gap = self.size_state.get("answer_box_gap", 3)
        scale = self.size_state.get("scale", 1.0) if self.size_state else 1.0
        is_compact = self.size_state.get("is_height_constrained", False)
        extra_pad = self.scale_value(16, scale, 8, 20)

        # Crear nuevas cajas si es necesario
        for i in range(len(self.answer_box_labels), word_length):
            box = ctk.CTkLabel(
                self.answer_boxes_frame,
                text="",
                font=self.answer_box_font,
                width=box_sz,
                height=box_sz,
                fg_color=self.COLORS["answer_box_empty"],
                corner_radius=8,
                text_color=self.COLORS["text_dark"],
            )
            self.answer_box_labels.append(box)

        revealed = self.wildcard_manager.get_revealed_positions()

        # Configurar cajas visibles
        for i in range(word_length):
            box = self.answer_box_labels[i]
            has_char = i < len(self.current_answer) and self.current_answer[i].strip()
            if has_char:
                fg = (
                    self.COLORS["success_green"]
                    if i in revealed
                    else self.COLORS["answer_box_filled"]
                )
                box.configure(
                    text=self.current_answer[i],
                    fg_color=fg,
                    width=box_sz,
                    height=box_sz,
                )
            else:
                box.configure(
                    text="",
                    fg_color=self.COLORS["answer_box_empty"],
                    width=box_sz,
                    height=box_sz,
                )
            box.grid(row=0, column=i, padx=gap, pady=4)

        # Ocultar y destruir cajas extras (prevenir crecimiento infinito de memoria)
        excess_count = len(self.answer_box_labels) - word_length
        if excess_count > 10:  # Threshold: keep up to 10 extras for reuse
            # Destroy the truly excess boxes beyond the threshold
            for i in range(word_length + 10, len(self.answer_box_labels)):
                try:
                    self.answer_box_labels[i].destroy()
                except tk.TclError:
                    pass
            del self.answer_box_labels[word_length + 10 :]

        # Hide remaining extra boxes
        for i in range(word_length, len(self.answer_box_labels)):
            self.answer_box_labels[i].grid_remove()

        # Actualizar tamaño del marco (relleno extra para evitar recorte en baja resolución)
        self.answer_boxes_frame.configure(
            width=max(box_sz, word_length * (box_sz + gap * 2)),
            height=box_sz + extra_pad,
        )
        if self.answer_boxes_frame and self.answer_boxes_frame.winfo_exists():
            if is_compact:
                pad_y = self.scale_value(8, scale, 6, 12)
            else:
                pad_y = self.scale_value(14, scale, 8, 28)
            self.answer_boxes_frame.grid_configure(pady=(pad_y, pad_y // 2))

    # =========================================================================
    # Manejo de Estado de Comodines
    # =========================================================================

    def update_charges_display(self):
        if self.charges_label:
            charges = self.wildcard_manager.get_charges()
            self.charges_label.configure(text=str(charges))

    def update_wildcard_buttons_state(self):
        charges = self.wildcard_manager.get_charges()
        double_blocked = self.wildcard_manager.is_double_points_blocked()
        others_blocked = self.wildcard_manager.are_other_wildcards_blocked()

        # Botón X2
        if self.wildcard_x2_btn:
            can_use_x2 = (
                charges >= self.wildcard_manager.COST_DOUBLE_POINTS
                and not double_blocked
            )
            mult = self.wildcard_manager.get_points_multiplier()
            btn_text = f"X{mult}" if mult > 1 else "X2"

            if can_use_x2:
                if self.wildcard_manager.is_double_points_active():
                    self.wildcard_x2_btn.configure(
                        text=btn_text,
                        fg_color=self.COLORS["wildcard_x2"],
                        hover_color=self.COLORS["wildcard_x2_hover"],
                        state="normal",
                    )
                else:
                    self.wildcard_x2_btn.configure(
                        text=btn_text,
                        fg_color=self.COLORS["wildcard_x2"],
                        hover_color=self.COLORS["wildcard_x2_hover"],
                        state="normal",
                    )
            else:
                self.wildcard_x2_btn.configure(
                    text=btn_text,
                    fg_color=self.COLORS["wildcard_disabled"],
                    hover_color=self.COLORS["wildcard_disabled"],
                    state="disabled",
                )

        # Botón de Pista
        if self.wildcard_hint_btn:
            can_use_hint = (
                charges >= self.wildcard_manager.COST_REVEAL_LETTER
                and not others_blocked
            )
            if can_use_hint:
                self.wildcard_hint_btn.configure(
                    fg_color=self.COLORS["wildcard_hint"],
                    hover_color=self.COLORS["wildcard_hint_hover"],
                    state="normal",
                )
            else:
                self.wildcard_hint_btn.configure(
                    fg_color=self.COLORS["wildcard_disabled"],
                    hover_color=self.COLORS["wildcard_disabled"],
                    state="disabled",
                )

        # Botón de Congelar
        if self.wildcard_freeze_btn:
            can_use_freeze = (
                charges >= self.wildcard_manager.COST_FREEZE_TIMER
                and not others_blocked
                and not self.wildcard_manager.is_timer_frozen()
            )
            if self.wildcard_manager.is_timer_frozen():
                self.wildcard_freeze_btn.configure(
                    fg_color=self.COLORS["wildcard_x2_active"],
                    hover_color=self.COLORS["wildcard_x2_active"],
                    state="disabled",
                )
            elif can_use_freeze:
                self.wildcard_freeze_btn.configure(
                    fg_color=self.COLORS["wildcard_freeze"],
                    hover_color=self.COLORS["wildcard_freeze_hover"],
                    state="normal",
                )
            else:
                self.wildcard_freeze_btn.configure(
                    fg_color=self.COLORS["wildcard_disabled"],
                    hover_color=self.COLORS["wildcard_disabled"],
                    state="disabled",
                )

        self.update_charges_display()

    def reset_wildcard_button_colors(self):
        self.update_wildcard_buttons_state()

    # =========================================================================
    # Estado Visual del Temporizador
    # =========================================================================

    def reset_timer_visuals(self):
        self.timer_frozen_visually = False
        if self.timer_label:
            self.timer_label.configure(text_color="white")
        if self.timer_icon_label and self.clock_icon:
            self.timer_icon_label.configure(image=self.clock_icon)

    def apply_freeze_timer_visuals(self):
        self.timer_frozen_visually = True
        if self.timer_label:
            self.timer_label.configure(text_color="#D0E7FF")
        if self.timer_icon_label and self.freeze_icon:
            self.timer_icon_label.configure(image=self.freeze_icon)

    def apply_double_points_visuals(self, multiplier=2):
        self.double_points_visually_active = True
        if self.score_label:
            self.score_label.configure(text_color=self.COLORS["warning_yellow"])
        if self.multiplier_label:
            self.multiplier_label.configure(text=f"X{multiplier}")
            self.multiplier_label.grid()

    def reset_double_points_visuals(self):
        self.double_points_visually_active = False
        if self.score_label:
            self.score_label.configure(text_color="white")
        if self.multiplier_label:
            self.multiplier_label.grid_remove()

    # =========================================================================
    # Métodos Abstractos (a ser sobrescritos en subclases)
    # =========================================================================

    def on_wildcard_x2(self):
        pass

    def on_wildcard_hint(self):
        pass

    def on_wildcard_freeze(self):
        pass

    def on_key_press(self, key):
        pass

    def on_skip(self):
        pass

    def on_check(self):
        pass

    def toggle_audio(self):
        pass

    def return_to_menu(self):
        pass

    def cleanup(self):
        pass

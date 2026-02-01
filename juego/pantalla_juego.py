import tkinter as tk

import customtkinter as ctk

from juego.pantalla_juego_config import GAME_PROFILES, GAME_RESIZE_DELAY
from juego.pantalla_juego_logica import GameScreenLogic


class GameScreen(GameScreenLogic):

    # Declaraciones de tipo para atributos heredados de clases padre
    resize_job: str | None
    key_feedback_job: str | None

    def __init__(
        self, parent, on_return_callback=None, tts_service=None, sfx_service=None
    ):
        super().__init__(parent, on_return_callback, tts_service, sfx_service)

        # Initialize keyboard binding IDs
        self._keypress_bind_id: str | None = None
        self._keyrelease_bind_id: str | None = None

        # Initialize image size tracking
        self.ultimo_tam_imagen: int = 0

        # Vincular evento de redimensionamiento
        self.parent.bind("<Configure>", self.on_resize)

        # Vincular teclado físico
        self.bind_physical_keyboard()

        # Layout responsivo inicial
        self.apply_responsive()

        # Iniciar el juego
        self.load_random_question()
        self.start_timer()

    def on_resize(self, event):
        if event.widget is not self.parent:
            return

        if self.resize_job:
            self.parent.after_cancel(self.resize_job)
        self.resize_job = self.parent.after(GAME_RESIZE_DELAY, self.apply_responsive)

    def apply_responsive(self):
        if not self.parent or not self.parent.winfo_exists():
            return

        # Obtener dimensiones actuales
        width, height = self.get_logical_dimensions()

        # Calcular escala usando perfil
        low_res_profile = GAME_PROFILES.get("low_res")
        scale = self.scaler.calculate_scale(width, height, low_res_profile)

        # Actualizar estado de tamaños
        self.size_state = self.size_calc.calculate_sizes(scale, width, height)
        self.apply_keyboard_scale_profile(height)
        needed_height = self.estimate_layout_height(self.size_state)
        if needed_height > height:
            fit_ratio = height / needed_height
            fit_scale = max(
                self.scaler.min_scale, min(self.scaler.max_scale, scale * fit_ratio)
            )
            self.size_state = self.size_calc.calculate_sizes(fit_scale, width, height)
            self.apply_keyboard_scale_profile(height)
            scale = fit_scale
            needed_height = self.estimate_layout_height(self.size_state)
        self.apply_keyboard_squeeze(needed_height, height)
        self.current_scale = scale
        self.current_window_width = width
        self.current_window_height = height

        # Actualizar todos los componentes
        self.update_fonts(scale)
        self.update_header(scale)
        self.update_question_container()
        self.update_keyboard()
        self.update_action_buttons(scale)
        self.update_wildcards(scale)

        # Redimensionar modales abiertos
        self.resize_modals(scale)

        # Limpiar trabajo de redimensionamiento
        self.resize_job = None

    def estimate_layout_height(self, sizes):
        scale = sizes.get("scale", 1.0)
        is_compact = sizes.get("is_height_constrained", False)

        header_h = sizes["header_height"]
        container_pad = sizes["container_pad_y"] * 2

        img_sz = sizes["image_size"]
        if is_compact:
            img_pad_top = self.scale_value(12, scale, 6, 20)
            img_pad_bottom = self.scale_value(6, scale, 3, 10)
        else:
            img_pad_top = self.scale_value(24, scale, 12, 60)
            img_pad_bottom = self.scale_value(12, scale, 6, 30)
        image_row = img_pad_top + img_sz + img_pad_bottom

        if is_compact:
            def_pad_y = sizes.get("definition_pad_y")
            def_height = sizes.get("definition_height")
        else:
            def_pad_y = sizes.get("definition_pad_y")
            def_height = sizes.get("definition_height")
        if def_pad_y is None:
            def_pad_y = self.scale_value(6 if is_compact else 14, scale, 3, 36)
        if def_height is None:
            if is_compact:
                def_height = self.scale_value(42, scale, 38, 50)
            else:
                if sizes.get("window_height", 0) >= 1080:
                    def_height = self.scale_value(70, scale, 50, 110)
                else:
                    def_height = self.scale_value(50, scale, 42, 65)
        definition_row = def_height + def_pad_y * 2

        box_sz = sizes["answer_box"]
        extra_pad = self.scale_value(16, scale, 8, 20)
        if is_compact:
            ab_pad = self.scale_value(8, scale, 6, 12)
        else:
            ab_pad = self.scale_value(14, scale, 8, 28)
        answer_row = box_sz + extra_pad + ab_pad + (ab_pad // 2)

        feedback_pad = sizes["feedback_pad_bottom"]
        if is_compact:
            feedback_pad = max(6, feedback_pad // 2)
        feedback_base = self.font_base_sizes.get("feedback", 14)
        feedback_min = self.font_min_sizes.get("feedback", 10)
        feedback_text = self.scale_value(
            feedback_base, scale, feedback_min, feedback_base * 2.5
        )
        feedback_buffer = self.scale_value(4, scale, 2, 8)
        feedback_row = feedback_pad + feedback_text + feedback_buffer

        left_height = image_row + definition_row + answer_row + feedback_row

        wc_sz = sizes["wildcard_size"]
        if is_compact:
            wc_pad_y = self.scale_value(10, scale, 6, 18)
            btn_gap = self.scale_value(6, scale, 3, 10)
            charges_pad = self.scale_value(10, scale, 4, 14)
        else:
            wc_pad_y = self.scale_value(28, scale, 16, 56)
            btn_gap = self.scale_value(10, scale, 6, 20)
            charges_pad = self.scale_value(14, scale, 8, 24)
        charges_h = max(sizes["lightning_icon"], sizes["charges_font"])
        wildcard_buttons_height = 3 * (wc_sz + btn_gap * 2)
        wildcards_height = (
            wc_pad_y * 2 + charges_h + charges_pad + wildcard_buttons_height
        )

        question_height = max(left_height, wildcards_height)

        keyboard_scale = sizes.get("keyboard_scale", 1.0)
        key_size = max(1, int(round(sizes["key_size"] * keyboard_scale)))
        key_row_gap = max(0, int(round(sizes["key_row_gap"] * keyboard_scale)))
        keyboard_pad_y = max(0, int(round(sizes["keyboard_pad_y"] * keyboard_scale)))
        keyboard_height = 3 * (key_size + key_row_gap * 2) + keyboard_pad_y
        action_height = sizes["action_button_height"] + self.scale_value(
            24, scale, 12, 48
        )

        return (
            header_h + container_pad + question_height + keyboard_height + action_height
        )

    def estimate_keyboard_height(self, sizes):
        keyboard_scale = sizes.get("keyboard_scale", 1.0)
        key_size = max(1, int(round(sizes["key_size"] * keyboard_scale)))
        key_row_gap = max(0, int(round(sizes["key_row_gap"] * keyboard_scale)))
        keyboard_pad_y = max(0, int(round(sizes["keyboard_pad_y"] * keyboard_scale)))
        return 3 * (key_size + key_row_gap * 2) + keyboard_pad_y

    def apply_keyboard_scale_profile(self, height):
        # Usar la altura real de ventana directamente para búsqueda de perfil
        # El parámetro height ya está en píxeles lógicos de winfo_height()
        # No se necesita ajuste de DPI - los umbrales del perfil están en píxeles lógicos
        profile = GAME_PROFILES.get("keyboard_scale", [])
        keyboard_scale = self.scaler.interpolate_profile(height, profile)
        keyboard_scale = self.scaler.clamp_value(keyboard_scale, 0.5, 1.0)
        if self.size_state is not None:
            self.size_state["keyboard_scale"] = keyboard_scale

    def apply_keyboard_squeeze(self, needed_height, height):
        if not self.size_state:
            return

        sizes = self.size_state
        kb_height = self.estimate_keyboard_height(sizes)
        if kb_height <= 0:
            return

        overflow = needed_height - height
        if overflow <= 0:
            return

        is_compact = sizes.get("is_height_constrained", False)
        min_ratio = 0.72 if is_compact else 0.8
        target_height = max(kb_height - overflow, kb_height * min_ratio)
        squeeze = max(min_ratio, min(1.0, target_height / kb_height))
        if squeeze >= 0.999:
            return

        sizes["key_size"] = max(16, int(round(sizes["key_size"] * squeeze)))
        sizes["key_gap"] = max(2, int(round(sizes["key_gap"] * squeeze)))
        sizes["key_row_gap"] = max(1, int(round(sizes["key_row_gap"] * squeeze)))
        sizes["keyboard_pad_y"] = max(4, int(round(sizes["keyboard_pad_y"] * squeeze)))
        sizes["delete_icon"] = max(12, int(round(sizes["delete_icon"] * squeeze)))

    def update_fonts(self, scale):
        self.font_registry.update_scale(scale, self.scaler)

    def update_header(self, scale):
        sizes = self.size_state

        # Altura del frame de encabezado
        if self.header_frame and self.header_frame.winfo_exists():
            self.header_frame.configure(height=sizes["header_height"])

        # Relleno del contenedor de encabezado
        pad_x = sizes["header_pad_x"]
        pad_y = sizes["header_pad_y"]

        if self.header_left_container and self.header_left_container.winfo_exists():
            self.header_left_container.grid_configure(padx=(pad_x, 0), pady=pad_y)

        if self.header_right_container and self.header_right_container.winfo_exists():
            self.header_right_container.grid_configure(padx=(0, pad_x), pady=pad_y)

        if self.header_center_container and self.header_center_container.winfo_exists():
            self.header_center_container.grid_configure(pady=pad_y)

        # Actualizar iconos del encabezado
        self.update_header_icons()

        # Actualizar botón de audio
        self.update_audio_button(scale)

    def update_header_icons(self):
        sizes = self.size_state

        # Icono de reloj
        if self.clock_icon:
            sz = sizes["timer_icon"]
            self.clock_icon.configure(size=(sz, sz))

        # Icono de estrella
        if self.star_icon:
            sz = sizes["star_icon"]
            self.star_icon.configure(size=(sz, sz))

        # Icono de congelar (para temporizador)
        if self.freeze_icon:
            sz = sizes["timer_icon"]
            self.freeze_icon.configure(size=(sz, sz))

    def update_audio_button(self, scale):
        sizes = self.size_state
        icon_sz = sizes["audio_icon"]
        btn_width = sizes["audio_button_width"]
        btn_height = sizes["audio_button_height"]
        corner_r = self.scale_value(8, scale, 6, 16)

        # Actualizar tamaños de iconos
        for icon in (self.audio_icon_on, self.audio_icon_off):
            if icon:
                icon.configure(size=(icon_sz, icon_sz))

        # Actualizar tamaño del botón
        if self.audio_toggle_btn and self.audio_toggle_btn.winfo_exists():
            self.audio_toggle_btn.configure(
                width=btn_width,
                height=btn_height,
                corner_radius=corner_r,
            )

    def update_question_container(self):
        sizes = self.size_state

        if not self.question_container or not self.question_container.winfo_exists():
            return

        # Relleno y radio de esquina del contenedor
        pad_x = sizes["container_pad_x"]
        pad_y = sizes["container_pad_y"]
        corner_r = sizes["container_corner_radius"]

        self.question_container.grid_configure(padx=pad_x, pady=pad_y)
        self.question_container.configure(corner_radius=corner_r)

        # Actualizar subcomponentes
        self.update_image()
        self.update_definition()
        self.update_answer_boxes()
        self.update_feedback()

    def update_image(self):
        sizes = self.size_state
        scale = sizes.get("scale", 1.0)
        is_compact = sizes.get("is_height_constrained", False)
        img_sz = sizes["image_size"]

        if self.image_frame and self.image_frame.winfo_exists():
            self.image_frame.configure(height=img_sz)
            # Escalar relleno de imagen - reducir en baja res, expandir en alta res
            if is_compact:
                pad_top = self.scale_value(12, scale, 6, 20)
                pad_bottom = self.scale_value(6, scale, 3, 10)
            else:
                pad_top = self.scale_value(24, scale, 12, 60)
                pad_bottom = self.scale_value(12, scale, 6, 30)
            self.image_frame.grid_configure(pady=(pad_top, pad_bottom))

        if self.image_label and self.image_label.winfo_exists():
            self.image_label.configure(width=img_sz, height=img_sz)

        # Recargar imagen solo si el tamanio cambio significativamente
        if self.current_image and self.current_question:
            nuevo_tam = self.size_state.get("image_size", img_sz)
            tam_actual = getattr(self, "ultimo_tam_imagen", 0)
            if abs(nuevo_tam - tam_actual) > 2:
                self.ultimo_tam_imagen = nuevo_tam
                self.load_question_image()

    def update_definition(self):
        sizes = self.size_state
        scale = sizes.get("scale", 1.0)

        # Actualizar relleno del frame de definición responsivamente
        if self.definition_frame and self.definition_frame.winfo_exists():
            pad_x = sizes.get("definition_pad_x")
            pad_y = sizes.get("definition_pad_y")
            if pad_x is None:
                pad_x = self.scale_value(36, scale, 20, 80)
            if pad_y is None:
                pad_y = self.scale_value(14, scale, 8, 36)
            self.definition_frame.grid_configure(padx=pad_x, pady=pad_y)

        # Actualizar altura del contenedor de scroll para definiciones largas
        if (
            self.definition_scroll_wrapper
            and self.definition_scroll_wrapper.winfo_exists()
        ):
            max_height = sizes.get("definition_height")
            if max_height is None:
                if sizes.get("is_height_constrained", False):
                    max_height = self.scale_value(42, scale, 38, 50)
                else:
                    if sizes.get("window_height", 0) >= 1080:
                        max_height = self.scale_value(70, scale, 50, 110)
                    else:
                        max_height = self.scale_value(50, scale, 42, 65)
            self.definition_scroll_wrapper.configure(height=max_height)

        if self.definition_label and self.definition_label.winfo_exists():
            wrap = sizes["definition_wrap"]
            self.definition_label.configure(wraplength=wrap)

        # Actualizar icono de información
        if self.info_icon:
            sz = sizes["info_icon"]
            self.info_icon.configure(size=(sz, sz))

        self.queue_definition_scroll_update()

    def update_answer_boxes(self):
        # Llamar al método padre para actualizar el texto de las casillas
        super().update_answer_boxes()

        sizes = self.size_state
        scale = sizes.get("scale", 1.0)
        is_compact = sizes.get("is_height_constrained", False)
        box_sz = sizes["answer_box"]
        gap = sizes["answer_box_gap"]
        extra_pad = self.scale_value(16, scale, 8, 20)

        # Actualizar etiquetas de casillas de respuesta
        # Usar grid_configure en un widget con grid_remove() lo volvería a mostrar!
        visible_boxes = [b for b in self.answer_box_labels if b.winfo_manager()]
        for box in visible_boxes:
            if box and box.winfo_exists():
                box.configure(width=box_sz, height=box_sz)
                box.grid_configure(padx=gap, pady=4)

        # Actualizar tamaño del frame si hay casillas visibles (altura extra para evitar recorte)
        if (
            visible_boxes
            and self.answer_boxes_frame
            and self.answer_boxes_frame.winfo_exists()
        ):
            frame_width = len(visible_boxes) * (box_sz + gap * 2)
            frame_height = box_sz + extra_pad
            self.answer_boxes_frame.configure(width=frame_width, height=frame_height)
            # Actualizar relleno del frame de casillas - reducir en baja res, expandir en alta res
            if is_compact:
                pad_y = self.scale_value(8, scale, 6, 12)
            else:
                pad_y = self.scale_value(14, scale, 8, 28)
            self.answer_boxes_frame.grid_configure(pady=(pad_y, pad_y // 2))

    def update_feedback(self):
        sizes = self.size_state
        is_compact = sizes.get("is_height_constrained", False)

        if self.feedback_label and self.feedback_label.winfo_exists():
            pad_bottom = sizes["feedback_pad_bottom"]
            # Reducir relleno de retroalimentación en baja res
            if is_compact:
                pad_bottom = max(6, pad_bottom // 2)
            self.feedback_label.grid_configure(pady=(0, pad_bottom))

    def update_keyboard(self):
        sizes = self.size_state
        key_sz = sizes["key_size"]
        key_gap = sizes["key_gap"]
        key_row_gap = sizes["key_row_gap"]
        keyboard_pad = sizes["keyboard_pad"]
        keyboard_pad_y = sizes["keyboard_pad_y"]
        keyboard_scale = sizes.get("keyboard_scale", 1.0)
        key_width_ratio = sizes.get("key_width_ratio", 1.0)

        if keyboard_scale < 1.0:
            key_sz = max(10, int(round(key_sz * keyboard_scale)))
            key_gap = max(1, int(round(key_gap * keyboard_scale)))
            key_row_gap = max(1, int(round(key_row_gap * keyboard_scale)))
            keyboard_pad = max(0, int(round(keyboard_pad * keyboard_scale)))
            keyboard_pad_y = max(2, int(round(keyboard_pad_y * keyboard_scale)))
            scale = sizes.get("scale", 1.0)
            base_size = self.font_base_sizes.get("keyboard", 18)
            min_size = self.font_min_sizes.get("keyboard", 10)
            new_size = max(min_size, int(round(base_size * scale * keyboard_scale)))
            self.keyboard_font.configure(size=new_size)
            delete_icon_sz = max(8, int(round(sizes["delete_icon"] * keyboard_scale)))
        else:
            delete_icon_sz = sizes["delete_icon"]
        delete_width = int(key_sz * sizes["delete_key_width_ratio"] * key_width_ratio)

        if self.keyboard_frame and self.keyboard_frame.winfo_exists():
            self.keyboard_frame.grid_configure(
                padx=keyboard_pad, pady=(0, keyboard_pad_y)
            )

        # Actualizar espaciado de filas del teclado
        for row_frame in self.keyboard_frame.winfo_children():
            if row_frame and row_frame.winfo_exists():
                row_frame.grid_configure(pady=key_row_gap)

        # Actualizar todos los botones del teclado
        for btn in self.keyboard_buttons:
            if btn and btn.winfo_exists():
                is_delete = btn is self.delete_button
                width = delete_width if is_delete else int(key_sz * key_width_ratio)
                btn.configure(width=width, height=key_sz)
                btn.grid_configure(padx=key_gap // 2)

        # Actualizar tamaño del icono de borrar
        if self.delete_icon:
            self.delete_icon.configure(size=(delete_icon_sz, delete_icon_sz))

    def update_action_buttons(self, scale):
        sizes = self.size_state
        btn_width = sizes["action_button_width"]
        btn_height = sizes["action_button_height"]
        btn_gap = sizes["action_button_gap"]
        corner_r = sizes["action_corner_radius"]

        for btn in [self.skip_button, self.check_button]:
            if btn and btn.winfo_exists():
                btn.configure(
                    width=btn_width,
                    height=btn_height,
                    corner_radius=corner_r,
                )
                btn.grid_configure(padx=btn_gap // 2)

        # Actualizar relleno del frame de botones de acción
        if self.action_buttons_frame and self.action_buttons_frame.winfo_exists():
            pad_bottom = self.scale_value(24, scale, 12, 48)
            self.action_buttons_frame.grid_configure(pady=(0, pad_bottom))

    def update_wildcards(self, scale):
        sizes = self.size_state
        is_compact = sizes.get("is_height_constrained", False)
        wc_sz = sizes["wildcard_size"]
        wc_corner = sizes["wildcard_corner_radius"]
        lightning_sz = sizes["lightning_icon"]
        freeze_sz = sizes["freeze_icon"]
        wc_font_size = sizes["wildcard_font"]
        charges_font_size = sizes["charges_font"]

        # Calcular ancho del botón igual que build_wildcards_panel
        wc_btn_width = int(wc_sz * 1.5)

        # Escalar espaciado de botones - reducir en baja res, expandir en alta res
        if is_compact:
            btn_gap = self.scale_value(6, scale, 3, 10)
        else:
            btn_gap = self.scale_value(10, scale, 6, 20)

        # Actualizar botones de comodines con forma de píldora consistente
        for btn in [
            self.wildcard_x2_btn,
            self.wildcard_hint_btn,
            self.wildcard_freeze_btn,
        ]:
            if btn and btn.winfo_exists():
                btn.configure(
                    width=wc_btn_width,
                    height=wc_sz,
                    corner_radius=wc_corner,
                )
                btn.grid_configure(pady=btn_gap)

        # Actualizar icono de rayo
        if self.lightning_icon:
            self.lightning_icon.configure(size=(lightning_sz, lightning_sz))

        # Actualizar icono de congelar de comodín
        if self.freeze_wildcard_icon:
            self.freeze_wildcard_icon.configure(size=(freeze_sz, freeze_sz))

        # Actualizar relleno del frame de comodines - más ajustado en baja res, expandir en alta res
        if self.wildcards_frame and self.wildcards_frame.winfo_exists():
            if is_compact:
                pad_x = self.scale_value(14, scale, 8, 20)
                pad_y = self.scale_value(10, scale, 6, 18)
            else:
                pad_x = self.scale_value(28, scale, 16, 56)
                pad_y = self.scale_value(28, scale, 16, 56)
            self.wildcards_frame.grid_configure(padx=(0, pad_x), pady=pad_y)

        # Actualizar relleno del frame de cargas
        if self.charges_frame and self.charges_frame.winfo_exists():
            charges_pad = (
                self.scale_value(10, scale, 4, 14)
                if is_compact
                else self.scale_value(14, scale, 8, 24)
            )
            self.charges_frame.grid_configure(pady=(0, charges_pad))

        # Actualizar fuentes de botones de comodines
        try:
            wc_font = ctk.CTkFont(
                family="Poppins ExtraBold", size=wc_font_size, weight="bold"
            )
            for btn in [self.wildcard_x2_btn, self.wildcard_hint_btn]:
                if btn and btn.winfo_exists():
                    btn.configure(font=wc_font)
        except tk.TclError:
            pass

        # Actualizar fuente de etiqueta de cargas
        if self.charges_label and self.charges_label.winfo_exists():
            try:
                charges_font = ctk.CTkFont(
                    family="Poppins SemiBold", size=charges_font_size, weight="bold"
                )
                self.charges_label.configure(font=charges_font)
            except tk.TclError:
                pass

        # Actualizar fuente de etiqueta de multiplicador
        if self.multiplier_label and self.multiplier_label.winfo_exists():
            mul_font_size = self.scale_value(20, scale, 12, 36)
            try:
                mul_font = ctk.CTkFont(
                    family="Poppins ExtraBold", size=mul_font_size, weight="bold"
                )
                self.multiplier_label.configure(font=mul_font)
            except tk.TclError:
                pass

    def resize_modals(self, scale):
        for modal_attr in ["completion_modal", "summary_modal", "skip_modal"]:
            modal = getattr(self, modal_attr, None)
            if modal and hasattr(modal, "modal") and modal.modal:
                try:
                    if modal.modal.winfo_exists():
                        if hasattr(modal, "resize"):
                            modal.resize(scale)
                except tk.TclError:
                    pass

    def return_to_menu(self):
        self.cleanup()
        if self.on_return_callback:
            self.on_return_callback()

    def cleanup(self):
        self.stop_timer()
        self.tts.stop()

        if self.feedback_animation_job:
            try:
                self.parent.after_cancel(self.feedback_animation_job)
            except (tk.TclError, ValueError):
                pass
            self.feedback_animation_job = None

        if self.key_feedback_job:
            try:
                self.parent.after_cancel(self.key_feedback_job)
            except (tk.TclError, ValueError):
                pass
            self.key_feedback_job = None

        # Cancel resize job
        if self.resize_job:
            try:
                self.parent.after_cancel(self.resize_job)
            except (tk.TclError, ValueError):
                pass
            self.resize_job = None

        # Cancel definition scroll update job
        if self.definition_scroll_update_job:
            try:
                self.parent.after_cancel(self.definition_scroll_update_job)
            except (tk.TclError, ValueError):
                pass
            self.definition_scroll_update_job = None

        self.close_all_modals()

        try:
            self.parent.unbind("<Configure>")
        except tk.TclError:
            pass
        self.unbind_physical_keyboard()

    def bind_physical_keyboard(self):
        root = self.parent.winfo_toplevel()
        # Store binding IDs to unbind only our specific handlers
        self._keypress_bind_id = root.bind("<KeyPress>", self.on_physical_key_press)
        self._keyrelease_bind_id = root.bind(
            "<KeyRelease>", self.on_physical_key_release
        )

    def unbind_physical_keyboard(self):
        try:
            root = self.parent.winfo_toplevel()
            # Unbind only our specific handlers using the stored IDs
            if hasattr(self, "_keypress_bind_id") and self._keypress_bind_id:
                root.unbind("<KeyPress>", self._keypress_bind_id)
                self._keypress_bind_id = None
            if hasattr(self, "_keyrelease_bind_id") and self._keyrelease_bind_id:
                root.unbind("<KeyRelease>", self._keyrelease_bind_id)
                self._keyrelease_bind_id = None
        except tk.TclError:
            pass

    def on_physical_key_press(self, event):
        if self.is_modal_open():
            return

        key_char = event.char.upper() if event.char else ""
        key_sym = event.keysym

        if key_sym == "Return":
            self.play_click_if_button_ready(self.check_button)
            self.simulate_button_press(self.check_button)
            self.on_check()
            return

        if self.awaiting_modal_decision:
            return

        if key_char.isalpha() and len(key_char) == 1:
            self.play_click_if_button_ready(self.key_button_map.get(key_char))
            self.show_key_feedback(key_char)
            self.on_key_press(key_char)
            return

        if key_sym == "BackSpace":
            self.play_click_if_button_ready(self.delete_button)
            self.show_key_feedback("⌫")
            self.on_key_press("⌫")
            return

        if key_sym == "Escape":
            self.play_click_if_button_ready(self.skip_button)
            self.simulate_button_press(self.skip_button)
            self.on_skip()
            return

    def play_click_if_button_ready(self, button):
        if not self.sfx or not button:
            return
        try:
            if button.cget("state") != "normal":
                return
        except tk.TclError:
            return
        self.sfx.play("click", stop_previous=True, volume=0.8)

    def on_physical_key_release(self, event):
        key_char = event.char.upper() if event.char else ""
        key_sym = event.keysym

        if key_char.isalpha() and len(key_char) == 1:
            self.reset_key_feedback(key_char)
            return

        if key_sym == "BackSpace":
            self.reset_key_feedback("⌫")
            return

    def show_key_feedback(self, key):
        if key in self.key_button_map:
            btn = self.key_button_map[key]
            if key == "⌫":
                btn.configure(fg_color=self.COLORS["danger_hover"])
            else:
                btn.configure(fg_color=self.COLORS["key_pressed"])

    def reset_key_feedback(self, key):
        if key in self.key_button_map:
            btn = self.key_button_map[key]
            if key == "⌫":
                btn.configure(fg_color=self.COLORS["danger_red"])
            else:
                btn.configure(fg_color=self.COLORS["key_bg"])

    def simulate_button_press(self, button):
        if button is None:
            return

        original_color = button.cget("fg_color")
        hover_color = button.cget("hover_color")

        button.configure(fg_color=hover_color)

        def reset():
            try:
                if button.winfo_exists():
                    button.configure(fg_color=original_color)
            except tk.TclError:
                pass

        self.parent.after(100, reset)

    def is_modal_open(self):
        for modal_attr in ["completion_modal", "summary_modal", "skip_modal"]:
            modal = getattr(self, modal_attr, None)
            if modal and hasattr(modal, "modal") and modal.modal:
                try:
                    if modal.modal.winfo_exists():
                        return True
                except tk.TclError:
                    pass
                # Limpiar referencia obsoleta si el modal ya no existe
                setattr(self, modal_attr, None)
        return False

    def close_all_modals(self):
        for modal_attr in ["completion_modal", "summary_modal", "skip_modal"]:
            modal = getattr(self, modal_attr, None)
            if modal:
                try:
                    modal.close()
                except (tk.TclError, AttributeError):
                    pass
                setattr(self, modal_attr, None)

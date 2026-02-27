from functools import partial

import customtkinter as ctk

from juego.pantalla_juego_config import KEYBOARD_LAYOUT


class GameUIBuilderMixin:

    def build_ui(self):
        # Limpiar widgets existentes
        for widget in self.parent.winfo_children():
            widget.destroy()

        # Configurar grid del padre
        self.parent.grid_rowconfigure(0, weight=1)
        self.parent.grid_columnconfigure(0, weight=1)

        # Contenedor principal
        self.main = ctk.CTkFrame(self.parent, fg_color=self.COLORS["bg_light"])
        self.main.grid(row=0, column=0, sticky="nsew")

        # Layout principal: encabezado, área de pregunta, teclado, botones de acción
        self.main.grid_rowconfigure(0, weight=0)  # Encabezado
        self.main.grid_rowconfigure(1, weight=1)  # Contenedor de pregunta
        self.main.grid_rowconfigure(2, weight=0)  # Teclado
        self.main.grid_rowconfigure(3, weight=0)  # Botones de acción
        self.main.grid_columnconfigure(0, weight=1)

        # Construir secciones
        self.build_header()
        self.build_question_container()
        self.build_keyboard()
        self.build_action_buttons()

    def build_header(self):
        header_height = self.BASE_SIZES["header_height"]

        self.header_frame = ctk.CTkFrame(
            self.main,
            fg_color=self.COLORS["header_bg"],
            height=header_height,
            corner_radius=0,
        )
        self.header_frame.grid(row=0, column=0, sticky="ew")
        self.header_frame.grid_propagate(False)

        # Distribución: temporizador izquierda, puntaje centro, silencio derecha
        self.header_frame.grid_columnconfigure(0, weight=1, uniform="header_side")
        self.header_frame.grid_columnconfigure(1, weight=0)
        self.header_frame.grid_columnconfigure(2, weight=1, uniform="header_side")
        self.header_frame.grid_rowconfigure(0, weight=1)

        # Cargar iconos del encabezado
        self.load_header_icons()

        # Contenedor izquierdo (temporizador)
        self.header_left_container = ctk.CTkFrame(
            self.header_frame, fg_color="transparent"
        )
        self.header_left_container.grid(
            row=0, column=0, sticky="w", padx=(self.BASE_SIZES["header_pad_x"], 0)
        )

        # Contenedor central (puntaje)
        self.header_center_container = ctk.CTkFrame(
            self.header_frame, fg_color="transparent"
        )
        self.header_center_container.grid(row=0, column=1)

        # Contenedor derecho (control de audio)
        self.header_right_container = ctk.CTkFrame(
            self.header_frame, fg_color="transparent"
        )
        self.header_right_container.grid(
            row=0, column=2, sticky="e", padx=(0, self.BASE_SIZES["header_pad_x"])
        )

        # Construir sección del temporizador
        self.build_timer_section()

        # Construir sección del puntaje
        self.build_score_section()

        # Construir control de audio
        self.build_audio_section()

    def build_timer_section(self):
        self.timer_container = ctk.CTkFrame(
            self.header_left_container, fg_color="transparent"
        )
        self.timer_container.grid(row=0, column=0)

        self.timer_icon_label = ctk.CTkLabel(
            self.timer_container, text="", image=self.clock_icon
        )
        self.timer_icon_label.grid(row=0, column=0, padx=(0, 8))

        self.timer_label = ctk.CTkLabel(
            self.timer_container,
            text="00:00",
            font=self.timer_font,
            text_color="white",
        )
        self.timer_label.grid(row=0, column=1)

    def build_score_section(self):
        self.score_container = ctk.CTkFrame(
            self.header_center_container, fg_color="transparent"
        )
        self.score_container.grid(row=0, column=0)

        star_sz = 24
        self.star_icon_label = ctk.CTkLabel(
            self.score_container,
            text="",
            image=self.star_icon,
            width=star_sz,
            height=star_sz,
        )
        self.star_icon_label.grid(row=0, column=0, padx=(0, 8))

        self.score_label = ctk.CTkLabel(
            self.score_container,
            text="0",
            font=self.score_font,
            text_color="white",
        )
        self.score_label.grid(row=0, column=1)

        # Etiqueta de multiplicador (oculta por defecto)
        self.multiplier_label = ctk.CTkLabel(
            self.score_container,
            text="",
            font=self.multiplier_font,
            text_color=self.COLORS["warning_yellow"],
            width=star_sz + 8,
        )
        self.multiplier_label.grid(row=0, column=2, padx=(8, 0))
        self.multiplier_label.grid_remove()

    def build_audio_section(self):
        self.audio_container = ctk.CTkFrame(
            self.header_right_container, fg_color="transparent"
        )
        self.audio_container.grid(row=0, column=0)

        self.load_audio_icons()

        self.audio_toggle_btn = ctk.CTkButton(
            self.audio_container,
            text="",
            image=self.audio_icon_on,
            font=self.timer_font,
            width=self.BASE_SIZES["audio_button_width"],
            height=self.BASE_SIZES["audio_button_height"],
            fg_color="transparent",
            hover_color=self.COLORS["header_hover"],
            text_color="white",
            corner_radius=8,
            command=self.toggle_audio,
        )
        self.audio_toggle_btn.grid(row=0, column=0)
        self.update_audio_button_icon()

    def build_question_container(self):
        self.question_container = ctk.CTkFrame(
            self.main,
            fg_color=self.COLORS["bg_card"],
            corner_radius=self.BASE_SIZES["container_corner_radius"],
            border_width=2,
            border_color=self.COLORS["border_light"],
        )
        self.question_container.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=self.BASE_SIZES["container_pad_x"],
            pady=self.BASE_SIZES["container_pad_y"],
        )

        # Configuración del grid del contenedor de pregunta
        # Todas las filas tienen weight=0 para que tomen alturas naturales según contenido
        # Esto evita que la fila de definición se comprima en resoluciones bajas
        self.question_container.grid_columnconfigure(0, weight=1)
        self.question_container.grid_columnconfigure(1, weight=0)
        for r in range(4):
            self.question_container.grid_rowconfigure(r, weight=0)

        # Construir secciones
        self.build_image_section()
        self.build_definition_section()
        self.build_answer_boxes_section()
        self.build_feedback_section()
        self.build_wildcards_panel()

    def build_image_section(self):
        img_sz = self.get_scaled_image_size()

        self.image_frame = ctk.CTkFrame(
            self.question_container, fg_color="transparent", height=img_sz
        )
        self.image_frame.grid(row=0, column=0, pady=(12, 6))
        self.image_frame.grid_rowconfigure(0, weight=1)
        self.image_frame.grid_columnconfigure(0, weight=1)

        self.image_label = ctk.CTkLabel(
            self.image_frame,
            text="",
            fg_color=self.COLORS["bg_light"],
            corner_radius=16,
            width=img_sz,
            height=img_sz,
        )
        self.image_label.grid(row=0, column=0)

    def build_definition_section(self):
        # Guardar referencia al frame para actualizaciones responsivas
        self.definition_frame = ctk.CTkFrame(
            self.question_container, fg_color="transparent"
        )
        self.definition_frame.grid(row=1, column=0, sticky="ew", padx=24, pady=2)
        self.definition_frame.grid_columnconfigure(0, weight=1)

        self.load_info_icon()

        # Contenedor con altura fija para limitar el frame con scroll
        self.definition_scroll_wrapper = ctk.CTkFrame(
            self.definition_frame,
            fg_color="transparent",
            height=45,
        )
        self.definition_scroll_wrapper.grid(row=0, column=0, sticky="ew")
        self.definition_scroll_wrapper.grid_propagate(False)  # Forzar altura fija
        self.definition_scroll_wrapper.grid_rowconfigure(0, weight=1)
        self.definition_scroll_wrapper.grid_columnconfigure(0, weight=1)

        # Frame con scroll dentro del contenedor
        self.definition_scroll = ctk.CTkScrollableFrame(
            self.definition_scroll_wrapper,
            fg_color="transparent",
            scrollbar_button_color="#9B9B9B",
            scrollbar_button_hover_color="#666666",
        )
        self.definition_scroll.grid(row=0, column=0, sticky="nsew")
        self.definition_scroll.grid_columnconfigure(0, weight=1)

        # Frame interno que centra contenido pero se expande horizontalmente
        self.def_inner = ctk.CTkFrame(self.definition_scroll, fg_color="transparent")
        self.def_inner.master.grid_columnconfigure(0, weight=1)
        self.def_inner.grid(row=0, column=0, sticky="")
        self.def_inner.grid_columnconfigure(1, weight=1)

        self.info_icon_label = ctk.CTkLabel(
            self.def_inner, text="", image=self.info_icon
        )
        self.info_icon_label.grid(row=0, column=0, sticky="n", padx=(0, 8), pady=(2, 0))

        self.definition_label = ctk.CTkLabel(
            self.def_inner,
            text="Loading question...",
            font=self.definition_font,
            text_color=self.COLORS["text_medium"],
            wraplength=self.BASE_SIZES["definition_wrap_base"],
            justify="left",
            anchor="w",
        )
        self.definition_label.grid(row=0, column=1, sticky="nw")

    def build_answer_boxes_section(self):
        box_sz = self.get_scaled_box_size()

        self.answer_boxes_frame = ctk.CTkFrame(
            self.question_container,
            fg_color="transparent",
            width=10 * (box_sz + 8),
            height=box_sz + 16,  # Relleno extra para evitar recorte en baja resolución
        )
        self.answer_boxes_frame.grid(row=2, column=0, pady=(6, 6), padx=20)
        # Configurar grid interno para centrar contenido sin estirar una sola columna
        self.answer_boxes_frame.grid_rowconfigure(0, weight=1)
        self.answer_boxes_frame.grid_anchor("center")

    def build_feedback_section(self):
        self.feedback_label = ctk.CTkLabel(
            self.question_container,
            text="",
            font=self.feedback_font,
            text_color=self.COLORS["feedback_correct"],
        )
        self.feedback_label.grid(row=3, column=0, pady=(0, 4), padx=20)

    def build_wildcards_panel(self):
        self.wildcards_frame = ctk.CTkFrame(
            self.question_container, fg_color="transparent"
        )
        # Usar sticky="n" para anclar arriba, altura natural del contenido
        self.wildcards_frame.grid(
            row=0, column=1, rowspan=4, sticky="n", padx=(0, 16), pady=12
        )

        wc_sz = self.BASE_SIZES["wildcard_size"]
        wc_font = self.BASE_SIZES["wildcard_font_size"]
        font = ctk.CTkFont(family="Poppins ExtraBold", size=wc_font, weight="bold")
        charges_font = ctk.CTkFont(family="Poppins SemiBold", size=14, weight="bold")

        # Calcular ancho del botón para acomodar texto como "X16" (multiplicadores acumulados)
        # Usar 1.5x la altura para una forma de píldora que ajuste todo el texto
        wc_btn_width = int(wc_sz * 1.5)
        wc_corner = (
            wc_sz // 2
        )  # Mantener radio de esquina basado en altura para forma de píldora

        # Mostrar cargas
        self.charges_frame = ctk.CTkFrame(self.wildcards_frame, fg_color="transparent")
        self.charges_frame.grid(row=1, column=0, pady=(0, 6))

        self.load_lightning_icon()
        if self.lightning_icon:
            self.lightning_icon_label = ctk.CTkLabel(
                self.charges_frame, text="", image=self.lightning_icon
            )
            self.lightning_icon_label.grid(row=0, column=0, padx=(0, 4))

        self.charges_label = ctk.CTkLabel(
            self.charges_frame,
            text=str(self.wildcard_manager.get_charges()),
            font=charges_font,
            text_color=self.COLORS["warning_yellow"],
        )
        self.charges_label.grid(row=0, column=1)

        # Botón X2 - usar ancho consistente para todos los botones
        self.wildcard_x2_btn = ctk.CTkButton(
            self.wildcards_frame,
            text="X2",
            font=font,
            width=wc_btn_width,
            height=wc_sz,
            corner_radius=wc_corner,
            fg_color=self.COLORS["wildcard_x2"],
            hover_color=self.COLORS["wildcard_x2_hover"],
            text_color="white",
            command=self.on_wildcard_x2,
        )
        self.wildcard_x2_btn.grid(row=2, column=0, pady=4)

        # Botón de pista - mismo ancho que X2 para consistencia
        self.wildcard_hint_btn = ctk.CTkButton(
            self.wildcards_frame,
            text="A",
            font=font,
            width=wc_btn_width,
            height=wc_sz,
            corner_radius=wc_corner,
            fg_color=self.COLORS["wildcard_hint"],
            hover_color=self.COLORS["wildcard_hint_hover"],
            text_color="white",
            command=self.on_wildcard_hint,
        )
        self.wildcard_hint_btn.grid(row=3, column=0, pady=4)

        # Botón de congelar - mismo ancho que los demás para consistencia
        self.load_freeze_wildcard_icon(int(wc_sz * 0.5))

        self.wildcard_freeze_btn = ctk.CTkButton(
            self.wildcards_frame,
            text="" if self.freeze_wildcard_icon else "❄",
            image=self.freeze_wildcard_icon,
            font=font,
            width=wc_btn_width,
            height=wc_sz,
            corner_radius=wc_corner,
            fg_color=self.COLORS["wildcard_freeze"],
            hover_color=self.COLORS["wildcard_freeze_hover"],
            text_color="white",
            command=self.on_wildcard_freeze,
        )
        self.wildcard_freeze_btn.grid(row=4, column=0, pady=4)

        self.update_wildcard_buttons_state()

    def build_keyboard(self):
        self.keyboard_frame = ctk.CTkFrame(self.main, fg_color="transparent")
        self.keyboard_frame.grid(
            row=2,
            column=0,
            pady=(0, 16),
            padx=self.BASE_SIZES["keyboard_pad_x"],
            sticky="ew",
        )
        self.keyboard_frame.grid_columnconfigure(0, weight=1)

        self.keyboard_buttons.clear()
        self.key_button_map.clear()
        self.delete_button = None
        self.load_delete_icon()

        key_sz = self.BASE_SIZES["key_base"]
        key_gap = self.BASE_SIZES["key_gap"]
        key_width_ratio = self.BASE_SIZES.get("key_width_ratio", 1.0)
        delete_ratio = self.BASE_SIZES.get("delete_key_width_ratio", 1.8)

        for row_idx, row_keys in enumerate(KEYBOARD_LAYOUT):
            row_frame = ctk.CTkFrame(self.keyboard_frame, fg_color="transparent")
            row_frame.grid(row=row_idx, column=0, pady=4, sticky="ew")
            row_frame.grid_columnconfigure(0, weight=1)
            row_frame.grid_columnconfigure(2, weight=1)

            inner = ctk.CTkFrame(row_frame, fg_color="transparent")
            inner.grid(row=0, column=1)

            for col, key in enumerate(row_keys):
                is_del = key == "⌫"
                w = (
                    int(key_sz * delete_ratio * key_width_ratio)
                    if is_del
                    else int(key_sz * key_width_ratio)
                )
                fg = self.COLORS["danger_red"] if is_del else self.COLORS["key_bg"]
                hv = self.COLORS["danger_hover"] if is_del else self.COLORS["key_hover"]
                tc = "white" if is_del else self.COLORS["text_dark"]
                img = self.delete_icon if is_del else None
                txt = "" if img else key

                btn = ctk.CTkButton(
                    inner,
                    text=txt,
                    image=img,
                    font=self.keyboard_font,
                    width=w,
                    height=key_sz,
                    fg_color=fg,
                    hover_color=hv,
                    text_color=tc,
                    border_width=2,
                    border_color=self.COLORS["header_bg"],
                    corner_radius=8,
                    command=partial(self.on_key_press, key),
                )
                btn.grid(row=0, column=col, padx=key_gap // 2)
                self.keyboard_buttons.append(btn)
                self.key_button_map[key] = btn
                if is_del:
                    self.delete_button = btn

    def build_action_buttons(self):
        self.action_buttons_frame = ctk.CTkFrame(self.main, fg_color="transparent")
        self.action_buttons_frame.grid(row=3, column=0, pady=(0, 24))

        btn_width = self.BASE_SIZES["action_button_width"]
        btn_height = self.BASE_SIZES["action_button_height"]
        btn_gap = self.BASE_SIZES["action_button_gap"]
        corner_r = self.BASE_SIZES["action_corner_radius"]

        self.skip_button = ctk.CTkButton(
            self.action_buttons_frame,
            text="Skip",
            font=self.button_font,
            width=btn_width,
            height=btn_height,
            fg_color=self.COLORS["bg_light"],
            hover_color=self.COLORS["border_medium"],
            text_color="black",
            border_width=2,
            border_color="black",
            corner_radius=corner_r,
            command=self.on_skip,
        )
        self.skip_button.grid(row=0, column=0, padx=btn_gap // 2)

        self.check_button = ctk.CTkButton(
            self.action_buttons_frame,
            text="Check",
            font=self.button_font,
            width=btn_width,
            height=btn_height,
            fg_color=self.COLORS["primary_blue"],
            hover_color=self.COLORS["primary_hover"],
            text_color="white",
            corner_radius=corner_r,
            command=self.on_check,
        )
        self.check_button.grid(row=0, column=1, padx=btn_gap // 2)

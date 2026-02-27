import customtkinter as ctk
from PIL import Image

from juego.modales_confirmacion import ConfirmationModal
from juego.pantalla_juego_config import LEVEL_BADGE_COLORS, MODAL_BASE_SIZES
from juego.pantalla_juego_modales_base import ModalBase

# Re-exportar para compatibilidad con versiones anteriores
__all__ = [
    "ModalBase",
    "GameCompletionModal",
    "QuestionSummaryModal",
    "SkipConfirmationModal",
    "ConfirmationModal",
]


class GameCompletionModal(ModalBase):
    def __init__(
        self,
        parent,
        final_score,
        total_questions,
        session_stats=None,
        on_previous_callback=None,
        has_previous=False,
        on_close_callback=None,
        initial_scale=1.0,
    ):
        super().__init__(parent, initial_scale)
        self.final_score = final_score
        self.total_questions = total_questions
        self.session_stats = session_stats or {}
        self.on_previous_callback = on_previous_callback
        self.has_previous = has_previous
        self.on_close_callback = on_close_callback
        self.star_icon = None

    def show(self):
        if self.modal and self.modal.winfo_exists():
            self.safe_try(self.lift_and_focus_modal)
            return
        self.show_with_scale()

    def show_with_scale(self, scale_override=None, attempt=0):
        root = self.parent.winfo_toplevel() if self.parent else None
        base_scale = self.calculate_scale_factor(root)
        scale = scale_override if scale_override is not None else base_scale
        self.current_scale = scale
        base_w, base_h = (
            MODAL_BASE_SIZES["completion_width"],
            MODAL_BASE_SIZES["completion_height"],
        )
        win_width, win_height = (
            self.get_logical_window_size(root, (base_w, base_h))
            if root
            else (base_w, base_h)
        )
        if root and win_width > 1 and win_height > 1:
            min_w = int(base_w * 0.85)
            min_h = int(base_h * 0.85)
            width = max(
                int(win_width * MODAL_BASE_SIZES["completion_width_ratio"]),
                min_w,
            )
            height = max(
                int(win_height * MODAL_BASE_SIZES["completion_height_ratio"]),
                min_h,
            )
            width = min(width, win_width)
            height = min(height, win_height)
            extra_h = int(base_h * 0.04)
            height = min(height + extra_h, win_height)
        else:
            width, height = base_w, base_h
        sizes = self.calc_sizes(scale, width, height)
        self.create_modal(width, height, "Game Complete")
        container = self.create_container(sizes["corner_r"], sizes["border_w"])
        self.create_header(
            container,
            "Game Complete",
            sizes["title_font"],
            sizes["header_h"],
            sizes["pad"],
        )
        content_wrapper = ctk.CTkFrame(
            container, fg_color=self.COLORS["bg_light"], corner_radius=0
        )
        content_wrapper.grid(row=1, column=0, sticky="nsew")
        content_wrapper.grid_rowconfigure(0, weight=1)
        content_wrapper.grid_columnconfigure(0, weight=1)
        content = ctk.CTkFrame(content_wrapper, fg_color="transparent")
        content.grid(row=0, column=0, sticky="", padx=sizes["pad"], pady=sizes["pad"])
        content.grid_columnconfigure(0, weight=1)
        self.build_content(content, width, sizes)
        self.modal.update_idletasks()
        # Forzar actualización de geometría para obtener medidas precisas
        content_wrapper.update_idletasks()
        content.update_idletasks()
        available_h = height - sizes["header_h"] - (sizes["border_w"] * 2)
        # Considerar relleno del contenedor y márgenes extra
        required_h = (
            content.winfo_reqheight()
            + (sizes["pad"] * 2)
            + (sizes["border_w"] * 2)
            + 16
        )
        # Reintentar con escala menor si el contenido no ajusta
        if attempt == 0 and available_h > 0 and required_h > available_h:
            shrink = (available_h - 10) / required_h  # Margen extra de seguridad
            if shrink < 0.96:
                target_scale = max(0.3, scale * shrink * 0.95)  # Reducción más agresiva
                self.close()
                self.show_with_scale(scale_override=target_scale, attempt=1)
                return
        self.modal.protocol("WM_DELETE_WINDOW", self.handle_close)
        self.modal.bind("<Escape>", self.handle_close)
        self.modal.bind("<Return>", self.handle_close)

    def calc_sizes(self, scale, modal_width, modal_height):
        base_w = MODAL_BASE_SIZES["completion_width"]
        base_h = MODAL_BASE_SIZES["completion_height"]
        w_scale = modal_width / base_w if base_w else 1.0
        h_scale = modal_height / base_h if base_h else 1.0
        modal_scale = min(w_scale, h_scale)
        effective_scale = min(scale, modal_scale)
        compact = modal_height < (base_h * 0.85)
        pad_min = 10 if compact else 14
        row_pad_min = 4 if compact else 6
        header_min = 40 if compact else 48
        btn_w_min = 110 if compact else 120
        btn_h_min = 30 if compact else 34
        score_min = 28 if compact else 32

        def sv(b, mn, mx):
            return self.scale_value(b, effective_scale, mn, mx)

        return {
            "title_font": self.make_font("Poppins ExtraBold", sv(28, 18, 48), "bold"),
            "message_font": self.make_font("Poppins SemiBold", sv(16, 12, 28), "bold"),
            "score_font": self.make_font(
                "Poppins ExtraBold", sv(54, score_min, 96), "bold"
            ),
            "label_font": self.make_font("Poppins SemiBold", sv(15, 11, 26), "bold"),
            "value_font": self.make_font("Poppins SemiBold", sv(15, 11, 26), "bold"),
            "badge_font": self.make_font("Poppins SemiBold", sv(14, 10, 24), "bold"),
            "footnote_font": self.make_font("Open Sans Regular", sv(13, 10, 22)),
            "button_font": self.make_font("Poppins SemiBold", sv(17, 13, 28), "bold"),
            "header_h": sv(72, header_min, 120),
            "btn_w": sv(180, btn_w_min, 300),
            "btn_h": sv(46, btn_h_min, 76),
            "btn_r": sv(12, 8, 20),
            "pad": sv(24, pad_min, 40),
            "row_pad": sv(10, row_pad_min, 18),
            "corner_r": sv(16, 12, 28),
            "border_w": sv(3, 2, 5),
            "card_corner_r": sv(14, 10, 24),
            "star_size": sv(32, 20, 56),
            "scale": effective_scale,
            "modal_scale": modal_scale,
            "compact": compact,
        }

    def build_content(self, content, width, s):
        stats = self.session_stats or {}

        def to_int(v, d=0):
            try:
                return int(v)
            except (TypeError, ValueError):
                return d

        total_q = to_int(
            stats.get("total_questions", self.total_questions),
            to_int(self.total_questions, 0),
        )
        answered = to_int(stats.get("questions_answered", total_q), 0)
        skipped = to_int(stats.get("questions_skipped"), 0)
        correct = stats.get("questions_correct")
        correct = (
            to_int(correct, max(0, answered - skipped))
            if correct is None
            else to_int(correct, 0)
        )
        errors = to_int(stats.get("total_errors"), 0)
        streak = to_int(stats.get("highest_streak", stats.get("clean_streak")), 0)
        grace = to_int(stats.get("grace_period_seconds", 5), 5)
        mastery_pct = stats.get("mastery_pct", 0.0)
        try:
            mastery_pct = float(mastery_pct)
        except (TypeError, ValueError):
            mastery_pct = 0.0
        knowledge_level = stats.get(
            "knowledge_level", self.knowledge_level_from_pct(mastery_pct)
        )
        level_color = LEVEL_BADGE_COLORS.get(knowledge_level, self.COLORS["text_light"])
        # Mensaje de completado
        ctk.CTkLabel(
            content,
            text="You've completed all questions!",
            font=s["message_font"],
            text_color=self.COLORS["text_light"],
            anchor="center",
        ).grid(row=0, column=0, pady=(0, s["row_pad"]))
        # Mostrar puntaje
        score_frame = ctk.CTkFrame(content, fg_color="transparent")
        score_frame.grid(row=1, column=0, pady=(0, s["row_pad"]))
        self.load_star_icon(s["star_size"])
        ctk.CTkLabel(
            score_frame,
            text="★" if not self.star_icon else "",
            image=self.star_icon,
            font=ctk.CTkFont(family="Segoe UI Symbol", size=s["star_size"]),
            text_color=self.COLORS["warning_yellow"],
        ).grid(row=0, column=0, padx=(0, 12))
        ctk.CTkLabel(
            score_frame,
            text=str(self.final_score),
            font=s["score_font"],
            text_color=self.COLORS["success_green"],
        ).grid(row=0, column=1)
        ctk.CTkLabel(
            score_frame,
            text="points",
            font=s["message_font"],
            text_color=self.COLORS["text_light"],
        ).grid(row=0, column=2, padx=(8, 0), sticky="s", pady=(0, 6))
        # Insignia de nivel de conocimiento
        badge_frame = ctk.CTkFrame(content, fg_color="transparent")
        badge_frame.grid(row=2, column=0, pady=(0, s["row_pad"]))
        ctk.CTkLabel(
            badge_frame,
            text="Knowledge Level:",
            font=s["label_font"],
            text_color=self.COLORS["text_dark"],
        ).grid(row=0, column=0, padx=(0, 8))
        ctk.CTkLabel(
            badge_frame,
            text=f" {knowledge_level} ",
            font=s["badge_font"],
            text_color=self.COLORS["text_white"],
            fg_color=level_color,
            corner_radius=6,
        ).grid(row=0, column=1, padx=(0, 8))
        ctk.CTkLabel(
            badge_frame,
            text=f"({mastery_pct:.1f}%)",
            font=s["badge_font"],
            text_color=self.COLORS["text_light"],
        ).grid(row=0, column=2)
        # Tarjeta de estadísticas
        stats_card = ctk.CTkFrame(
            content,
            fg_color=self.COLORS["bg_card"],
            corner_radius=s["card_corner_r"],
            border_width=1,
            border_color=self.COLORS["border_light"],
        )
        stats_card.grid(row=3, column=0, sticky="ew", pady=(0, s["pad"] // 2))
        stats_card.grid_columnconfigure(0, weight=1)
        rows_container = ctk.CTkFrame(stats_card, fg_color="transparent")
        rows_container.grid(
            row=0, column=0, sticky="nsew", padx=s["pad"], pady=s["pad"] // 2
        )
        rows_container.grid_columnconfigure(0, weight=1)
        rows = [
            ("Total questions", str(total_q), self.COLORS["primary_blue"]),
            ("Correct", str(correct), self.COLORS["success_green"]),
            ("Skipped", str(skipped), self.COLORS["warning_yellow"]),
            ("Errors", str(errors), self.COLORS["danger_red"]),
            ("Highest streak", str(streak), self.COLORS["level_master"]),
        ]
        self.animated_widgets.clear()
        self.widget_target_colors.clear()
        bg = self.COLORS["bg_light"]
        for i, (lbl, val, clr) in enumerate(rows):
            rf = ctk.CTkFrame(rows_container, fg_color="transparent")
            rf.grid(row=i, column=0, sticky="ew", pady=s["row_pad"] // 2)
            rf.grid_columnconfigure(0, weight=1)
            rf.grid_columnconfigure(1, weight=0)
            lw = ctk.CTkLabel(
                rf, text=f"{lbl}:", font=s["label_font"], text_color=bg, anchor="w"
            )
            lw.grid(row=0, column=0, sticky="w")
            self.widget_target_colors[id(lw)] = self.COLORS["text_dark"]
            vw = ctk.CTkLabel(
                rf, text=val, font=s["value_font"], text_color=bg, anchor="e"
            )
            vw.grid(row=0, column=1, sticky="e", padx=(s["pad"] // 2, 0))
            self.widget_target_colors[id(vw)] = clr
            self.animated_widgets.append((lw, vw))
        # Nota del período de gracia
        grace_text = (
            f"You get the first {grace} seconds free to read the clue. "
            "Time-based scoring starts after that."
        )
        ctk.CTkLabel(
            content,
            text=grace_text,
            font=s["footnote_font"],
            text_color=self.COLORS["text_light"],
            justify="center",
            anchor="center",
            wraplength=int(width * (0.9 if s.get("compact") else 0.82)),
        ).grid(row=4, column=0, pady=(0, s["pad"] // 2))
        # Botones
        btn_container = ctk.CTkFrame(content, fg_color="transparent")
        btn_container.grid(row=5, column=0, pady=(s["pad"] // 2, 0))
        ctk.CTkButton(
            btn_container,
            text="Previous Question",
            font=s["button_font"],
            fg_color=self.COLORS["header_bg"] if self.has_previous else "#E8E8E8",
            hover_color=self.COLORS["header_bg"] if self.has_previous else "#E8E8E8",
            text_color=self.COLORS["text_white"] if self.has_previous else "#AAAAAA",
            command=self.handle_previous if self.has_previous else None,
            state="normal" if self.has_previous else "disabled",
            width=s["btn_w"],
            height=s["btn_h"],
            corner_radius=s["btn_r"],
        ).grid(row=0, column=0, padx=(0, s["pad"] // 2))
        rb = ctk.CTkButton(
            btn_container,
            text="Return to Menu",
            font=s["button_font"],
            width=s["btn_w"],
            height=s["btn_h"],
            fg_color=self.COLORS["primary_blue"],
            hover_color=self.COLORS["primary_hover"],
            text_color=self.COLORS["text_white"],
            corner_radius=s["btn_r"],
            command=self.handle_close,
        )
        rb.grid(row=0, column=1, padx=(s["pad"] // 2, 0))
        self.safe_try(rb.focus_set)
        self.start_fade_in_animation(bg)

    def load_star_icon(self, size):
        img = self.load_svg_image(self.IMAGES_DIR / "star.svg", self.SVG_RASTER_SCALE)
        if img:
            r, g, b = (
                int(self.COLORS["warning_yellow"][1:3], 16),
                int(self.COLORS["warning_yellow"][3:5], 16),
                int(self.COLORS["warning_yellow"][5:7], 16),
            )
            ir, ig, ib, ia = img.split()
            img = Image.merge(
                "RGBA",
                (
                    self.apply_channel_tint(ir, r),
                    self.apply_channel_tint(ig, g),
                    self.apply_channel_tint(ib, b),
                    ia,
                ),
            )
            self.star_icon = ctk.CTkImage(
                light_image=img, dark_image=img, size=(size, size)
            )

    def apply_channel_tint(self, channel, component):
        def tint_value(value):
            return int(value * component / 255)

        return channel.point(tint_value)

    def knowledge_level_from_pct(self, mastery_pct):
        pct = max(0.0, min(100.0, float(mastery_pct)))
        if pct < 40:
            return "Beginner"
        if pct < 55:
            return "Student"
        if pct < 70:
            return "Professional"
        if pct < 85:
            return "Expert"
        return "Master"

    def handle_previous(self, _event=None):
        self.close()
        if self.on_previous_callback:
            self.on_previous_callback()

    def handle_close(self, _event=None):
        self.close()
        if self.on_close_callback:
            self.on_close_callback()


class QuestionSummaryModal(ModalBase):
    def __init__(
        self,
        parent,
        correct_word,
        time_taken,
        points_awarded,
        total_score,
        on_next_callback,
        on_close_callback=None,
        on_previous_callback=None,
        has_previous=False,
        multiplier=1,
        on_main_menu_callback=None,
        streak=0,
        streak_multiplier=1.0,
        charges_earned=0,
        charges_max_reached=False,
        initial_scale=1.0,
    ):
        super().__init__(parent, initial_scale)
        self.correct_word = correct_word
        self.time_taken = time_taken
        self.points_awarded = points_awarded
        self.total_score = total_score
        self.on_next_callback = on_next_callback
        self.on_close_callback = on_close_callback
        self.on_previous_callback = on_previous_callback
        self.has_previous = has_previous
        self.multiplier = multiplier
        self.on_main_menu_callback = on_main_menu_callback
        self.streak = streak
        self.streak_multiplier = streak_multiplier
        self.charges_earned = charges_earned
        self.charges_max_reached = charges_max_reached
        self.confirmation_modal = None
        self.next_button = None

    def show(self):
        if self.modal and self.modal.winfo_exists():
            self.safe_try(self.lift_and_focus_modal)
            return
        root = self.parent.winfo_toplevel() if self.parent else None
        win_width, win_height = (
            self.get_logical_window_size(root, (1280, 720)) if root else (1280, 720)
        )
        self.current_scale = self.calculate_scale_factor(root)
        scale = self.current_scale
        width_ratio, height_ratio = (
            MODAL_BASE_SIZES["summary_width_ratio"],
            MODAL_BASE_SIZES["summary_height_ratio"],
        )
        if root and win_width > 1 and win_height > 1:
            width, height = int(win_width * width_ratio), int(win_height * height_ratio)
        else:
            width, height = (
                MODAL_BASE_SIZES["summary_width"],
                MODAL_BASE_SIZES["summary_height"],
            )
        max_scale = MODAL_BASE_SIZES.get("summary_max_scale", 1.6)
        max_width = int(MODAL_BASE_SIZES["summary_width"] * max_scale)
        max_height = int(MODAL_BASE_SIZES["summary_height"] * max_scale)
        width = min(width, max_width)
        height = min(height, max_height)
        sizes = self.calc_sizes(scale, width, height)
        self.create_modal(width, height, "Summary")
        container = self.create_container(sizes["corner_r"], sizes["border_w"])
        self.create_header(
            container, "Summary", sizes["title_font"], sizes["header_h"], sizes["pad"]
        )
        content_wrapper = ctk.CTkFrame(
            container, fg_color=self.COLORS["bg_light"], corner_radius=0
        )
        content_wrapper.grid(row=1, column=0, sticky="nsew")
        content_wrapper.grid_rowconfigure(0, weight=1)
        content_wrapper.grid_columnconfigure(0, weight=1)
        content = ctk.CTkFrame(content_wrapper, fg_color="transparent")
        content.grid(
            row=0, column=0, sticky="", padx=sizes["pad"], pady=sizes["pad"] // 2
        )
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=1)
        # Construir filas de datos
        points_display = str(self.points_awarded)
        streak_display = f"{self.streak} ({self.streak_multiplier:.2f}x)"
        if self.charges_earned > 0:
            charges_display, charges_color = (
                f"+{self.charges_earned}",
                self.COLORS["warning_yellow"],
            )
        elif self.charges_max_reached:
            charges_display, charges_color = "0 (max)", self.COLORS["text_light"]
        else:
            charges_display, charges_color = "0", self.COLORS["text_light"]
        rows = [
            ("Word:", self.correct_word, self.COLORS["primary_blue"]),
            ("Time:", f"{self.time_taken}s", self.COLORS["primary_blue"]),
            ("Points:", points_display, self.COLORS["primary_blue"]),
            ("Total:", str(self.total_score), self.COLORS["primary_blue"]),
            ("Streak:", streak_display, self.COLORS["level_master"]),
            ("Charges:", charges_display, charges_color),
        ]
        self.animated_widgets.clear()
        self.widget_target_colors.clear()
        bg = self.COLORS["bg_light"]
        for i, (lbl, val, clr) in enumerate(rows):
            row_frame = ctk.CTkFrame(content, fg_color="transparent")
            row_frame.grid(
                row=i, column=0, columnspan=2, sticky="ew", pady=sizes["row_pad"]
            )
            row_frame.grid_columnconfigure(0, weight=1)
            row_frame.grid_columnconfigure(1, weight=1)
            lw = ctk.CTkLabel(
                row_frame, text=lbl, font=sizes["label_font"], text_color=bg, anchor="e"
            )
            lw.grid(row=0, column=0, sticky="e", padx=(0, 4))
            self.widget_target_colors[id(lw)] = self.COLORS["text_dark"]
            if lbl == "Points:" and self.multiplier > 1:
                value_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
                value_frame.grid(row=0, column=1, sticky="w")
                vw = ctk.CTkLabel(
                    value_frame,
                    text=val,
                    font=sizes["value_font"],
                    text_color=bg,
                    anchor="w",
                )
                vw.grid(row=0, column=0, sticky="w")
                self.widget_target_colors[id(vw)] = clr
                mult_font = self.make_font(
                    "Poppins ExtraBold",
                    max(8, sizes["value_font"].cget("size") - 2),
                    "bold",
                )
                mult_label = ctk.CTkLabel(
                    value_frame,
                    text=f"x{self.multiplier}",
                    font=mult_font,
                    text_color=bg,
                    anchor="w",
                )
                mult_label.grid(row=0, column=1, padx=(3, 0), sticky="w")
                self.widget_target_colors[id(mult_label)] = self.COLORS[
                    "warning_yellow"
                ]
                self.animated_widgets.append((lw, vw))
                self.animated_widgets.append((mult_label, mult_label))
            else:
                vw = ctk.CTkLabel(
                    row_frame,
                    text=val,
                    font=sizes["value_font"],
                    text_color=bg,
                    anchor="w",
                )
                vw.grid(row=0, column=1, sticky="w")
                self.widget_target_colors[id(vw)] = clr
                self.animated_widgets.append((lw, vw))
        # Botones
        btn_container = ctk.CTkFrame(content, fg_color="transparent")
        btn_container.grid(row=6, column=0, columnspan=2, pady=(sizes["pad"], 0))
        btn_container.grid_columnconfigure((0, 1, 2), weight=1)
        btn_gap = max(2, sizes["pad"] // 3)
        menu_gap = max(btn_gap, sizes["pad"] // 2)
        if sizes["modal_scale"] >= 1.2:
            menu_gap = max(menu_gap, sizes["pad"])
        ctk.CTkButton(
            btn_container,
            text="Previous",
            font=sizes["button_font"],
            fg_color=self.COLORS["header_bg"] if self.has_previous else "#E8E8E8",
            hover_color=self.COLORS["header_bg"] if self.has_previous else "#E8E8E8",
            text_color=self.COLORS["text_white"] if self.has_previous else "#AAAAAA",
            command=self.handle_previous if self.has_previous else None,
            state="normal" if self.has_previous else "disabled",
            width=sizes["btn_w"],
            height=sizes["btn_h"],
            corner_radius=sizes["btn_r"],
        ).grid(row=0, column=0, padx=(0, btn_gap))
        ctk.CTkButton(
            btn_container,
            text="Close",
            font=sizes["button_font"],
            fg_color="#D0D6E0",
            hover_color="#B8C0D0",
            text_color=self.COLORS["text_white"],
            command=self.handle_close,
            width=sizes["btn_w"],
            height=sizes["btn_h"],
            corner_radius=sizes["btn_r"],
        ).grid(row=0, column=1, padx=btn_gap)
        self.next_button = ctk.CTkButton(
            btn_container,
            text="Next",
            font=sizes["button_font"],
            fg_color=self.COLORS["primary_blue"],
            hover_color=self.COLORS["primary_hover"],
            text_color=self.COLORS["text_white"],
            command=self.handle_next,
            width=sizes["btn_w"],
            height=sizes["btn_h"],
            corner_radius=sizes["btn_r"],
        )
        self.next_button.grid(row=0, column=2, padx=(btn_gap, 0))
        ctk.CTkButton(
            btn_container,
            text="Main Menu",
            font=sizes["button_font"],
            fg_color=self.COLORS["header_bg"],
            hover_color="#2D3444",
            text_color=self.COLORS["text_white"],
            command=self.handle_main_menu,
            width=sizes["btn_w"],
            height=sizes["btn_h"],
            corner_radius=sizes["btn_r"],
        ).grid(row=1, column=0, columnspan=3, pady=(menu_gap, 0))
        self.modal.protocol("WM_DELETE_WINDOW", self.handle_close)
        self.modal.bind("<Escape>", self.handle_close)
        self.modal.bind("<Return>", self.handle_next)
        self.modal.bind("<KP_Enter>", self.handle_next)
        self.safe_try(self.modal.focus_force)
        self.safe_try(self.next_button.focus_set)
        self.start_fade_in_animation(bg)

    def calc_sizes(self, scale, modal_width, modal_height):
        w_scale, h_scale = (
            modal_width / MODAL_BASE_SIZES["summary_width"],
            modal_height / MODAL_BASE_SIZES["summary_height"],
        )
        m_scale = min(w_scale, h_scale)

        def sz(b, mn, mx):
            return int(max(mn, min(mx, b * m_scale)))

        return {
            "title_font": self.make_font("Poppins ExtraBold", sz(20, 12, 36), "bold"),
            "label_font": self.make_font("Poppins SemiBold", sz(13, 9, 22), "bold"),
            "value_font": self.make_font("Poppins SemiBold", sz(13, 9, 22), "bold"),
            "button_font": self.make_font("Poppins SemiBold", sz(12, 9, 22), "bold"),
            "header_h": sz(50, 30, 90),
            "btn_w": sz(100, 60, 180),
            "btn_h": sz(34, 22, 60),
            "btn_r": sz(8, 4, 16),
            "pad": sz(14, 6, 28),
            "row_pad": sz(4, 1, 10),
            "corner_r": sz(12, 6, 24),
            "border_w": sz(2, 1, 4),
            "scale": scale,
            "modal_scale": m_scale,
        }

    def handle_next(self, _event=None):
        self.close()
        if self.on_next_callback:
            self.on_next_callback()

    def handle_close(self, _event=None):
        self.close()
        if self.on_close_callback:
            self.on_close_callback()

    def handle_previous(self, _event=None):
        self.close()
        if self.on_previous_callback:
            self.on_previous_callback()

    def handle_main_menu(self):
        self.close()
        self.confirmation_modal = ConfirmationModal(
            self.parent,
            "Return to Main Menu",
            "Are you sure you want to return to the main menu?",
            on_confirm_callback=self.on_main_menu_confirmed,
            on_cancel_callback=self.on_main_menu_cancelled,
            confirm_text="Yes",
            cancel_text="No",
            initial_scale=self.current_scale,
        )
        self.confirmation_modal.show()

    def on_main_menu_confirmed(self):
        if self.on_main_menu_callback:
            self.on_main_menu_callback()

    def on_main_menu_cancelled(self):
        self.show()


class SkipConfirmationModal(ModalBase):
    def __init__(self, parent, on_skip_callback, initial_scale=1.0):
        super().__init__(parent, initial_scale)
        self.on_skip_callback = on_skip_callback

    def show(self):
        if self.modal and self.modal.winfo_exists():
            self.safe_try(self.lift_and_focus_modal)
            return
        root = self.parent.winfo_toplevel() if self.parent else None
        self.current_scale = self.calculate_scale_factor(root)
        scale = self.current_scale
        if root and root.winfo_width() > 1:
            root_w, root_h = self.get_logical_window_size(root)
            width = int(root_w * MODAL_BASE_SIZES["skip_width_ratio"])
            height = int(root_h * MODAL_BASE_SIZES["skip_height_ratio"])
        else:
            width, height = (
                MODAL_BASE_SIZES["skip_width"],
                MODAL_BASE_SIZES["skip_height"],
            )
        sizes = self.calc_sizes(scale)
        self.create_modal(width, height, "Skip Question")
        container = self.create_container(sizes["corner_r"], sizes["border_w"])
        self.create_header(
            container,
            "Skip Question",
            sizes["title_font"],
            sizes["header_h"],
            sizes["pad"],
        )
        content_wrapper = ctk.CTkFrame(
            container, fg_color=self.COLORS["bg_light"], corner_radius=0
        )
        content_wrapper.grid(row=1, column=0, sticky="nsew")
        content_wrapper.grid_rowconfigure(0, weight=1)
        content_wrapper.grid_rowconfigure(1, weight=0)
        content_wrapper.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            content_wrapper,
            text="Are you sure you want to skip the question? No points will be awarded.",
            font=sizes["body_font"],
            text_color=self.COLORS["text_dark"],
            justify="center",
            anchor="center",
            wraplength=int(width * 0.8),
        ).grid(row=0, column=0, sticky="nsew", pady=sizes["pad"], padx=sizes["pad"])
        btn_frame = ctk.CTkFrame(content_wrapper, fg_color="transparent")
        btn_frame.grid(row=1, column=0, pady=(0, sizes["pad"]))
        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            font=sizes["button_font"],
            fg_color="#D0D6E0",
            hover_color="#B8C0D0",
            text_color=self.COLORS["text_white"],
            command=self.close,
            width=sizes["btn_w"],
            height=sizes["btn_h"],
            corner_radius=sizes["btn_r"],
        ).grid(row=0, column=0, padx=(0, sizes["pad"]))
        ctk.CTkButton(
            btn_frame,
            text="Skip",
            font=sizes["button_font"],
            fg_color=self.COLORS["danger_red"],
            hover_color=self.COLORS["danger_hover"],
            text_color=self.COLORS["text_white"],
            command=self.handle_skip,
            width=sizes["btn_w"],
            height=sizes["btn_h"],
            corner_radius=sizes["btn_r"],
        ).grid(row=0, column=1, padx=(sizes["pad"], 0))
        self.modal.protocol("WM_DELETE_WINDOW", self.close)
        self.modal.bind("<Escape>", self.handle_close)

    def calc_sizes(self, scale):
        def sv(b, mn, mx):
            return self.scale_value(b, scale, mn, mx)

        return {
            "title_font": self.make_font("Poppins ExtraBold", sv(24, 16, 40), "bold"),
            "body_font": self.make_font("Poppins SemiBold", sv(16, 12, 28), "bold"),
            "button_font": self.make_font("Poppins SemiBold", sv(16, 12, 28), "bold"),
            "header_h": sv(72, 48, 120),
            "btn_w": sv(120, 80, 200),
            "btn_h": sv(44, 32, 72),
            "btn_r": sv(12, 8, 20),
            "pad": sv(24, 16, 40),
            "corner_r": sv(16, 12, 28),
            "border_w": sv(3, 2, 5),
        }

    def handle_skip(self, _event=None):
        self.close()
        if self.on_skip_callback:
            self.on_skip_callback()

    def handle_close(self, _event=None):
        self.close()

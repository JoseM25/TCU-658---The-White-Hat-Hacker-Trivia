import os
import tkinter as tk

import customtkinter as ctk
from PIL import Image, ImageTk
from tksvg import SvgImage as TkSvgImage

from juego.pantalla_juego_config import (
    GAME_COLORS,
    LEVEL_BADGE_COLORS,
    MODAL_ANIMATION,
    MODAL_BASE_SIZES,
)


class ModalBase:
    COLORS = GAME_COLORS
    IMAGES_DIR = os.path.join("recursos", "imagenes")
    SVG_RASTER_SCALE = 2.0

    # Animation settings
    ANIMATION_DELAY_MS = MODAL_ANIMATION["delay_ms"]
    FADE_STEPS = MODAL_ANIMATION["fade_steps"]
    FADE_STEP_MS = MODAL_ANIMATION["fade_step_ms"]

    def __init__(self, parent, initial_scale=1.0):
        self.parent = parent
        self.modal = None
        self.root = None
        self.animation_jobs = []
        self.animated_widgets = []
        self.widget_target_colors = {}
        self.current_scale = initial_scale

        # Widget references for resizing
        self.resizable_widgets = {}
        self.resizable_fonts = {}

    def calculate_scale_factor(self, root):
        if not root or not root.winfo_exists():
            return 1.0
        try:
            width, height = root.winfo_width(), root.winfo_height()
        except tk.TclError:
            return 1.0
        if width <= 1 or height <= 1:
            return 1.0
        return max(0.5, min(2.2, width / 1280, height / 720))

    def create_modal(self, width, height, title):
        root = self.parent.winfo_toplevel() if self.parent else None
        self.root = root

        self.modal = ctk.CTkToplevel(root if root else self.parent)
        self.modal.after_cancel(self.modal.after(0, lambda: None))
        self.modal.iconphoto(False, tk.PhotoImage(width=1, height=1))

        # Get scaling for position calculation
        try:
            scaling = ctk.ScalingTracker.get_window_scaling(root) if root else 1.0
        except (AttributeError, KeyError):
            scaling = 1.0

        # Calculate position
        if root and root.winfo_width() > 1 and root.winfo_height() > 1:
            pos_x = root.winfo_rootx() + (root.winfo_width() - width) // 2
            pos_y = root.winfo_rooty() + (root.winfo_height() - height) // 2
        else:
            pos_x = (self.modal.winfo_screenwidth() - width) // 2
            pos_y = (self.modal.winfo_screenheight() - height) // 2

        pos_x = int(pos_x / scaling)
        pos_y = int(pos_y / scaling)

        self.modal.geometry(f"{width}x{height}+{pos_x}+{pos_y}")
        self.modal.attributes("-topmost", False)
        self.modal.title(title)

        if root:
            self.modal.transient(root)
            self.modal.grab_set()

        self.modal.resizable(False, False)
        self.modal.configure(fg_color=self.COLORS["bg_light"])
        self.modal.grid_rowconfigure(0, weight=1)
        self.modal.grid_columnconfigure(0, weight=1)

        return root

    def scale_value(self, base, scale=None, min_val=None, max_val=None):
        value = base * (scale or self.current_scale)
        if min_val is not None:
            value = max(min_val, value)
        if max_val is not None:
            value = min(max_val, value)
        return int(round(value))

    def create_container(self, corner_r, border_w):
        container = ctk.CTkFrame(
            self.modal,
            fg_color=self.COLORS["bg_light"],
            corner_radius=corner_r,
            border_width=border_w,
            border_color="#1D6CFF",
        )
        container.grid(row=0, column=0, sticky="nsew")
        container.grid_rowconfigure(0, weight=0)
        container.grid_rowconfigure(1, weight=1)
        container.grid_columnconfigure(0, weight=1)
        return container

    def create_header(self, container, title, title_font, header_h, pad):
        header = ctk.CTkFrame(
            container,
            fg_color=self.COLORS["header_bg"],
            corner_radius=0,
            height=header_h,
        )
        header.grid(row=0, column=0, sticky="new")
        header.grid_propagate(False)
        header.grid_columnconfigure(0, weight=1)
        header.grid_rowconfigure(0, weight=1)

        label = ctk.CTkLabel(
            header,
            text=title,
            font=title_font,
            text_color=self.COLORS["text_white"],
            anchor="center",
        )
        label.grid(row=0, column=0, sticky="nsew", padx=pad)

        self.resizable_widgets["header"] = header
        self.resizable_widgets["header_title"] = label
        self.resizable_fonts["header_title"] = title_font

        return header

    def interpolate_color(self, start_hex, end_hex, progress):
        sr = int(start_hex[1:3], 16)
        sg = int(start_hex[3:5], 16)
        sb = int(start_hex[5:7], 16)
        er = int(end_hex[1:3], 16)
        eg = int(end_hex[3:5], 16)
        eb = int(end_hex[5:7], 16)
        r = int(sr + (er - sr) * progress)
        g = int(sg + (eg - sg) * progress)
        b = int(sb + (eb - sb) * progress)
        return f"#{r:02x}{g:02x}{b:02x}"

    def start_fade_in_animation(self, bg_color):
        for row_index, (label_widget, value_widget) in enumerate(self.animated_widgets):
            delay = row_index * self.ANIMATION_DELAY_MS
            job = self.modal.after(
                delay,
                lambda lw=label_widget, vw=value_widget, bg=bg_color: self.fade_in_row(
                    lw, vw, bg, 0
                ),
            )
            self.animation_jobs.append(job)

    def fade_in_row(self, label_widget, value_widget, bg_color, step):
        if not self.modal or not self.modal.winfo_exists():
            return

        label_target = self.widget_target_colors.get(id(label_widget))
        value_target = self.widget_target_colors.get(id(value_widget))

        if step >= self.FADE_STEPS:
            self.safe_try(lambda: label_widget.configure(text_color=label_target))
            self.safe_try(lambda: value_widget.configure(text_color=value_target))
            return

        progress = (step + 1) / self.FADE_STEPS
        label_color = self.interpolate_color(bg_color, label_target, progress)
        value_color = self.interpolate_color(bg_color, value_target, progress)

        self.safe_try(lambda: label_widget.configure(text_color=label_color))
        self.safe_try(lambda: value_widget.configure(text_color=value_color))

        job = self.modal.after(
            self.FADE_STEP_MS,
            lambda: self.fade_in_row(label_widget, value_widget, bg_color, step + 1),
        )
        self.animation_jobs.append(job)

    def load_svg_image(self, svg_path, scale=1.0):
        try:
            svg_photo = TkSvgImage(file=str(svg_path), scale=scale)
            return ImageTk.getimage(svg_photo).convert("RGBA")
        except (FileNotFoundError, ValueError):
            return None

    def close(self):
        modal = self.modal
        for job in self.animation_jobs:
            if modal:
                self.safe_try(lambda j=job, m=modal: m.after_cancel(j))
        self.animation_jobs.clear()
        self.animated_widgets.clear()
        self.widget_target_colors.clear()
        if modal:
            try:
                if modal.winfo_exists():
                    self.safe_try(modal.grab_release)
                    self.safe_try(modal.destroy)
            except tk.TclError:
                pass
        self.modal = None
        self.root = None

    def safe_try(self, func):
        try:
            func()
        except tk.TclError:
            pass

    def resize(self, scale):
        self.current_scale = scale


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
            self.safe_try(lambda: (self.modal.lift(), self.modal.focus_force()))
            return

        root = self.parent.winfo_toplevel() if self.parent else None

        # Calculate scale from root
        self.current_scale = self.calculate_scale_factor(root)
        scale = self.current_scale

        # Calculate dimensions based on scale
        base_w, base_h = (
            MODAL_BASE_SIZES["completion_width"],
            MODAL_BASE_SIZES["completion_height"],
        )

        if root and root.winfo_width() > 1:
            width = max(
                int(root.winfo_width() * MODAL_BASE_SIZES["completion_width_ratio"]),
                480,
            )
            height = max(
                int(root.winfo_height() * MODAL_BASE_SIZES["completion_height_ratio"]),
                400,
            )
        else:
            width, height = base_w, base_h

        # Calculate sizes
        sizes = self._calc_sizes(scale)

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

        self._build_content(content, width, sizes)

        self.modal.protocol("WM_DELETE_WINDOW", self.handle_close)
        self.modal.bind("<Escape>", lambda e: self.handle_close())
        self.modal.bind("<Return>", lambda e: self.handle_close())

    def _calc_sizes(self, scale):
        return {
            "title_font": ctk.CTkFont(
                family="Poppins ExtraBold",
                size=self.scale_value(28, scale, 18, 48),
                weight="bold",
            ),
            "message_font": ctk.CTkFont(
                family="Poppins SemiBold",
                size=self.scale_value(16, scale, 12, 28),
                weight="bold",
            ),
            "score_font": ctk.CTkFont(
                family="Poppins ExtraBold",
                size=self.scale_value(54, scale, 32, 96),
                weight="bold",
            ),
            "label_font": ctk.CTkFont(
                family="Poppins SemiBold",
                size=self.scale_value(15, scale, 11, 26),
                weight="bold",
            ),
            "value_font": ctk.CTkFont(
                family="Poppins SemiBold",
                size=self.scale_value(15, scale, 11, 26),
                weight="bold",
            ),
            "badge_font": ctk.CTkFont(
                family="Poppins SemiBold",
                size=self.scale_value(14, scale, 10, 24),
                weight="bold",
            ),
            "footnote_font": ctk.CTkFont(
                family="Open Sans Regular", size=self.scale_value(13, scale, 10, 22)
            ),
            "button_font": ctk.CTkFont(
                family="Poppins SemiBold",
                size=self.scale_value(17, scale, 13, 28),
                weight="bold",
            ),
            "header_h": self.scale_value(72, scale, 48, 120),
            "btn_w": self.scale_value(180, scale, 120, 300),
            "btn_h": self.scale_value(46, scale, 34, 76),
            "btn_r": self.scale_value(12, scale, 8, 20),
            "pad": self.scale_value(24, scale, 14, 40),
            "row_pad": self.scale_value(10, scale, 6, 18),
            "corner_r": self.scale_value(16, scale, 12, 28),
            "border_w": self.scale_value(3, scale, 2, 5),
            "card_corner_r": self.scale_value(14, scale, 10, 24),
            "star_size": self.scale_value(32, scale, 20, 56),
            "scale": scale,
        }

    def _build_content(self, content, width, s):
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
            "knowledge_level", self._knowledge_level_from_pct(mastery_pct)
        )
        level_color = LEVEL_BADGE_COLORS.get(knowledge_level, self.COLORS["text_light"])

        # Completion message
        ctk.CTkLabel(
            content,
            text="You've completed all questions!",
            font=s["message_font"],
            text_color=self.COLORS["text_light"],
            anchor="center",
        ).grid(row=0, column=0, pady=(0, s["row_pad"]))

        # Score display
        score_frame = ctk.CTkFrame(content, fg_color="transparent")
        score_frame.grid(row=1, column=0, pady=(0, s["row_pad"]))

        self._load_star_icon(s["star_size"])
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

        # Knowledge level badge
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

        # Stats card
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

        # Grace period note
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
            wraplength=int(width * 0.82),
        ).grid(row=4, column=0, pady=(0, s["pad"] // 2))

        # Buttons
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

    def _load_star_icon(self, size):
        img = self.load_svg_image(
            os.path.join(self.IMAGES_DIR, "star.svg"), self.SVG_RASTER_SCALE
        )
        if img:
            r = int(self.COLORS["warning_yellow"][1:3], 16)
            g = int(self.COLORS["warning_yellow"][3:5], 16)
            b = int(self.COLORS["warning_yellow"][5:7], 16)
            ir, ig, ib, ia = img.split()
            img = Image.merge(
                "RGBA",
                (
                    ir.point(lambda x: int(x * r / 255)),
                    ig.point(lambda x: int(x * g / 255)),
                    ib.point(lambda x: int(x * b / 255)),
                    ia,
                ),
            )
            self.star_icon = ctk.CTkImage(
                light_image=img, dark_image=img, size=(size, size)
            )

    def _knowledge_level_from_pct(self, mastery_pct):
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

    def handle_previous(self):
        self.close()
        if self.on_previous_callback:
            self.on_previous_callback()

    def handle_close(self):
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

    def show(self):
        if self.modal and self.modal.winfo_exists():
            self.safe_try(lambda: (self.modal.lift(), self.modal.focus_force()))
            return

        root = self.parent.winfo_toplevel() if self.parent else None

        # Calculate scale
        self.current_scale = self.calculate_scale_factor(root)
        scale = self.current_scale

        # Calculate dimensions
        if root and root.winfo_width() > 1:
            width = int(root.winfo_width() * MODAL_BASE_SIZES["summary_width_ratio"])
            height = int(root.winfo_height() * MODAL_BASE_SIZES["summary_height_ratio"])
        else:
            width = MODAL_BASE_SIZES["summary_width"]
            height = MODAL_BASE_SIZES["summary_height"]

        sizes = self._calc_sizes(scale)

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
        content.grid(row=0, column=0, sticky="")
        content.grid_columnconfigure(0, weight=1)

        # Build data rows
        points_display = str(self.points_awarded)
        streak_display = f"{self.streak} ({self.streak_multiplier:.2f}x)"

        if self.charges_earned > 0:
            charges_display = f"+{self.charges_earned}"
            charges_color = self.COLORS["warning_yellow"]
        elif self.charges_max_reached:
            charges_display = "0 (max reached)"
            charges_color = self.COLORS["text_light"]
        else:
            charges_display = "0"
            charges_color = self.COLORS["text_light"]

        rows = [
            ("Correct Word:", self.correct_word, self.COLORS["primary_blue"]),
            ("Time Taken:", f"{self.time_taken}s", self.COLORS["primary_blue"]),
            ("Points Awarded:", points_display, self.COLORS["primary_blue"]),
            ("Total Score:", str(self.total_score), self.COLORS["primary_blue"]),
            ("Streak:", streak_display, self.COLORS["level_master"]),
            ("Charges won:", charges_display, charges_color),
        ]

        self.animated_widgets.clear()
        self.widget_target_colors.clear()
        bg = self.COLORS["bg_light"]

        for i, (lbl, val, clr) in enumerate(rows):
            lw = ctk.CTkLabel(
                content,
                text=lbl,
                font=sizes["label_font"],
                text_color=bg,
                anchor="center",
            )
            lw.grid(row=i * 2, column=0, pady=(sizes["row_pad"], 0))
            self.widget_target_colors[id(lw)] = self.COLORS["text_dark"]

            # Special handling for Points Awarded with multiplier
            if lbl == "Points Awarded:" and self.multiplier > 1:
                value_frame = ctk.CTkFrame(content, fg_color="transparent")
                value_frame.grid(row=i * 2 + 1, column=0, pady=(0, sizes["row_pad"]))

                vw = ctk.CTkLabel(
                    value_frame,
                    text=val,
                    font=sizes["value_font"],
                    text_color=bg,
                    anchor="center",
                )
                vw.grid(row=0, column=0)
                self.widget_target_colors[id(vw)] = clr

                mult_font = ctk.CTkFont(
                    family="Poppins ExtraBold",
                    size=self.scale_value(13, scale, 10, 22),
                    weight="bold",
                )
                mult_label = ctk.CTkLabel(
                    value_frame,
                    text=f"x{self.multiplier}",
                    font=mult_font,
                    text_color=bg,
                    anchor="center",
                )
                mult_label.grid(row=0, column=1, padx=(6, 0))
                self.widget_target_colors[id(mult_label)] = self.COLORS[
                    "warning_yellow"
                ]

                self.animated_widgets.append((lw, vw))
                self.animated_widgets.append((mult_label, mult_label))
            else:
                vw = ctk.CTkLabel(
                    content,
                    text=val,
                    font=sizes["value_font"],
                    text_color=bg,
                    anchor="center",
                )
                vw.grid(row=i * 2 + 1, column=0, pady=(0, sizes["row_pad"]))
                self.widget_target_colors[id(vw)] = clr

                self.animated_widgets.append((lw, vw))

        # Buttons
        btn_container = ctk.CTkFrame(content, fg_color="transparent")
        btn_container.grid(row=12, column=0, pady=(sizes["pad"], 0))
        btn_container.grid_columnconfigure((0, 1, 2), weight=1)

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
        ).grid(row=0, column=0, padx=(0, sizes["pad"] // 2))

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
        ).grid(row=0, column=1, padx=sizes["pad"] // 2)

        ctk.CTkButton(
            btn_container,
            text="Next Question",
            font=sizes["button_font"],
            fg_color=self.COLORS["primary_blue"],
            hover_color=self.COLORS["primary_hover"],
            text_color=self.COLORS["text_white"],
            command=self.handle_next,
            width=sizes["btn_w"],
            height=sizes["btn_h"],
            corner_radius=sizes["btn_r"],
        ).grid(row=0, column=2, padx=(sizes["pad"] // 2, 0))

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
        ).grid(row=1, column=0, columnspan=3, pady=(sizes["pad"] // 2, 0))

        self.modal.protocol("WM_DELETE_WINDOW", self.handle_close)
        self.modal.bind("<Escape>", lambda e: self.handle_close())
        self.modal.bind("<Return>", lambda e: self.handle_next())

        self.start_fade_in_animation(bg)

    def _calc_sizes(self, scale):
        return {
            "title_font": ctk.CTkFont(
                family="Poppins ExtraBold",
                size=self.scale_value(26, scale, 16, 44),
                weight="bold",
            ),
            "label_font": ctk.CTkFont(
                family="Poppins SemiBold",
                size=self.scale_value(15, scale, 11, 26),
                weight="bold",
            ),
            "value_font": ctk.CTkFont(
                family="Poppins SemiBold",
                size=self.scale_value(15, scale, 11, 26),
                weight="bold",
            ),
            "button_font": ctk.CTkFont(
                family="Poppins SemiBold",
                size=self.scale_value(16, scale, 12, 28),
                weight="bold",
            ),
            "header_h": self.scale_value(66, scale, 44, 110),
            "btn_w": self.scale_value(150, scale, 100, 250),
            "btn_h": self.scale_value(44, scale, 32, 72),
            "btn_r": self.scale_value(12, scale, 8, 20),
            "pad": self.scale_value(20, scale, 12, 36),
            "row_pad": self.scale_value(6, scale, 4, 12),
            "corner_r": self.scale_value(16, scale, 12, 28),
            "border_w": self.scale_value(3, scale, 2, 5),
            "scale": scale,
        }

    def handle_next(self):
        self.close()
        if self.on_next_callback:
            self.on_next_callback()

    def handle_close(self):
        self.close()
        if self.on_close_callback:
            self.on_close_callback()

    def handle_previous(self):
        self.close()
        if self.on_previous_callback:
            self.on_previous_callback()

    def handle_main_menu(self):
        self.close()
        if self.on_main_menu_callback:
            self.on_main_menu_callback()


class SkipConfirmationModal(ModalBase):

    def __init__(self, parent, on_skip_callback, initial_scale=1.0):
        super().__init__(parent, initial_scale)
        self.on_skip_callback = on_skip_callback

    def show(self):
        if self.modal and self.modal.winfo_exists():
            self.safe_try(lambda: (self.modal.lift(), self.modal.focus_force()))
            return

        root = self.parent.winfo_toplevel() if self.parent else None

        # Calculate scale
        self.current_scale = self.calculate_scale_factor(root)
        scale = self.current_scale

        # Calculate dimensions
        if root and root.winfo_width() > 1:
            width = int(root.winfo_width() * MODAL_BASE_SIZES["skip_width_ratio"])
            height = int(root.winfo_height() * MODAL_BASE_SIZES["skip_height_ratio"])
        else:
            width = MODAL_BASE_SIZES["skip_width"]
            height = MODAL_BASE_SIZES["skip_height"]

        sizes = self._calc_sizes(scale)

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
        self.modal.bind("<Escape>", lambda e: self.close())

    def _calc_sizes(self, scale):
        return {
            "title_font": ctk.CTkFont(
                family="Poppins ExtraBold",
                size=self.scale_value(24, scale, 16, 40),
                weight="bold",
            ),
            "body_font": ctk.CTkFont(
                family="Poppins SemiBold",
                size=self.scale_value(16, scale, 12, 28),
                weight="bold",
            ),
            "button_font": ctk.CTkFont(
                family="Poppins SemiBold",
                size=self.scale_value(16, scale, 12, 28),
                weight="bold",
            ),
            "header_h": self.scale_value(72, scale, 48, 120),
            "btn_w": self.scale_value(120, scale, 80, 200),
            "btn_h": self.scale_value(44, scale, 32, 72),
            "btn_r": self.scale_value(12, scale, 8, 20),
            "pad": self.scale_value(24, scale, 16, 40),
            "corner_r": self.scale_value(16, scale, 12, 28),
            "border_w": self.scale_value(3, scale, 2, 5),
        }

    def handle_skip(self):
        self.close()
        if self.on_skip_callback:
            self.on_skip_callback()

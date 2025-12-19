import json
import os
import random
import tkinter as tk

import customtkinter as ctk
from PIL import Image, ImageTk
from tksvg import SvgImage as TkSvgImage

from juego.comodines import WildcardManager
from juego.logica import ScoringSystem
from juego.tts_service import TTSService


class GameCompletionModal:

    COLORS = {
        "bg_light": "#F5F7FA",
        "header_bg": "#202632",
        "text_white": "#FFFFFF",
        "text_dark": "#3A3F4B",
        "text_medium": "#7A7A7A",
        "primary_blue": "#005DFF",
        "primary_hover": "#003BB8",
        "success_green": "#00CFC5",
        "warning_yellow": "#FFC553",
        "danger_red": "#FF4F60",
        "border_blue": "#1D6CFF",
        "card_bg": "#FFFFFF",
        "border_light": "#E2E7F3",
        "master_purple": "#7C3AED",
    }

    IMAGES_DIR = os.path.join("recursos", "imagenes")
    SVG_RASTER_SCALE = 2.0

    LEVEL_BADGE_COLORS = {
        "Beginner": COLORS["danger_red"],
        "Student": COLORS["primary_blue"],
        "Professional": COLORS["success_green"],
        "Expert": "#CC9A42",
        "Master": COLORS["master_purple"],
    }

    ANIMATION_DELAY_MS = 160  # Delay between each row appearing
    FADE_STEPS = 12  # Number of steps for fade animation
    FADE_STEP_MS = 30  # Milliseconds per fade step

    def __init__(
        self,
        parent,
        final_score,
        total_questions,
        session_stats=None,
        on_previous_callback=None,
        has_previous=False,
        on_close_callback=None,
    ):
        self.parent = parent
        self.final_score = final_score
        self.total_questions = total_questions
        self.session_stats = session_stats or {}
        self.on_previous_callback = on_previous_callback
        self.has_previous = has_previous
        self.on_close_callback = on_close_callback
        self.modal = None
        self.root = None
        self.animation_jobs = []  # Track scheduled animations for cleanup
        self.animated_widgets = []  # Widgets to animate
        self.widget_target_colors = {}  # Store target colors for animation
        self.star_icon = None  # Will hold the CTkImage for the star

    def show(self):
        if self.modal and self.modal.winfo_exists():
            self.safe_try(lambda: (self.modal.lift(), self.modal.focus_force()))
            return

        root = self.parent.winfo_toplevel() if self.parent else None

        base_w, base_h = 560, 520
        if root and root.winfo_width() > 1 and root.winfo_height() > 1:
            width = int(root.winfo_width() * 0.42)
            height = int(root.winfo_height() * 0.52)
        else:
            width, height = base_w, base_h

        width = max(width, 480)
        height = max(height, 400)

        scale = min(width / base_w, height / base_h) * 0.90

        title_size = max(int(28 * scale), 18)
        message_size = max(int(16 * scale), 12)
        score_size = max(int(54 * scale), 32)
        label_size = max(int(15 * scale), 11)
        value_size = max(int(15 * scale), 11)
        footnote_size = max(int(13 * scale), 10)
        button_size = max(int(17 * scale), 13)

        header_h = max(int(72 * scale), 48)
        btn_w = max(int(180 * scale), 120)
        btn_h = max(int(46 * scale), 34)
        btn_r = max(int(12 * scale), 8)
        pad = max(int(24 * scale), 14)
        row_pad = max(int(10 * scale), 6)
        corner_r = max(int(16 * scale), 12)
        border_w = max(int(3 * scale), 2)
        card_corner_r = max(int(14 * scale), 10)

        title_font = ctk.CTkFont(
            family="Poppins ExtraBold", size=title_size, weight="bold"
        )
        message_font = ctk.CTkFont(
            family="Poppins SemiBold", size=message_size, weight="bold"
        )
        score_font = ctk.CTkFont(
            family="Poppins ExtraBold", size=score_size, weight="bold"
        )
        label_font = ctk.CTkFont(
            family="Poppins SemiBold", size=label_size, weight="bold"
        )
        value_font = ctk.CTkFont(
            family="Poppins SemiBold", size=value_size, weight="bold"
        )
        footnote_font = ctk.CTkFont(family="Open Sans Regular", size=footnote_size)
        button_font = ctk.CTkFont(
            family="Poppins SemiBold", size=button_size, weight="bold"
        )

        self.root = root
        self.modal = ctk.CTkToplevel(root if root else self.parent)
        self.modal.after_cancel(
            self.modal.after(0, lambda: None)
        )  # Cancel CTk's icon update
        self.modal.iconphoto(False, tk.PhotoImage(width=1, height=1))  # Blank icon

        # Get scaling factor - geometry() applies this internally, so we divide
        try:
            scaling = ctk.ScalingTracker.get_window_scaling(root) if root else 1.0
        except (AttributeError, KeyError):
            scaling = 1.0

        # Calculate centered position in screen coordinates
        if root and root.winfo_width() > 1 and root.winfo_height() > 1:
            pos_x = root.winfo_rootx() + (root.winfo_width() - width) // 2
            pos_y = root.winfo_rooty() + (root.winfo_height() - height) // 2
        else:
            screen_w = self.modal.winfo_screenwidth()
            screen_h = self.modal.winfo_screenheight()
            pos_x = (screen_w - width) // 2
            pos_y = (screen_h - height) // 2

        # Divide by scaling since CTk's geometry() multiplies internally
        pos_x = int(pos_x / scaling)
        pos_y = int(pos_y / scaling)

        self.modal.geometry(f"{width}x{height}+{pos_x}+{pos_y}")

        # Disable the appear-on-top behavior that CTkToplevel does
        self.modal.attributes("-topmost", False)

        self.modal.title("Game Complete")

        if root:
            self.modal.transient(root)
            self.modal.grab_set()  # Use grab instead of disabling root
        self.modal.resizable(False, False)
        self.modal.configure(fg_color=self.COLORS["bg_light"])
        self.modal.grid_rowconfigure(0, weight=1)
        self.modal.grid_columnconfigure(0, weight=1)

        container = ctk.CTkFrame(
            self.modal,
            fg_color=self.COLORS["bg_light"],
            corner_radius=corner_r,
            border_width=border_w,
            border_color=self.COLORS["border_blue"],
        )
        container.grid(row=0, column=0, sticky="nsew")
        container.grid_rowconfigure(0, weight=0)
        container.grid_rowconfigure(1, weight=1)
        container.grid_columnconfigure(0, weight=1)

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

        ctk.CTkLabel(
            header,
            text="Game Complete",
            font=title_font,
            text_color=self.COLORS["text_white"],
            anchor="center",
        ).grid(row=0, column=0, sticky="nsew", padx=pad)

        content_wrapper = ctk.CTkFrame(
            container,
            fg_color=self.COLORS["bg_light"],
            corner_radius=0,
        )
        content_wrapper.grid(row=1, column=0, sticky="nsew")
        content_wrapper.grid_rowconfigure(0, weight=1)
        content_wrapper.grid_columnconfigure(0, weight=1)

        content = ctk.CTkFrame(content_wrapper, fg_color="transparent")
        content.grid(row=0, column=0, sticky="", padx=pad, pady=pad)
        content.grid_columnconfigure(0, weight=1)

        stats = self.session_stats or {}

        def to_int(value, default=0):
            try:
                return int(value)
            except (TypeError, ValueError):
                return default

        total_questions = to_int(
            stats.get("total_questions", self.total_questions),
            default=to_int(self.total_questions, 0),
        )
        questions_answered = to_int(stats.get("questions_answered", total_questions), 0)

        questions_skipped = to_int(stats.get("questions_skipped"), 0)
        questions_correct = stats.get("questions_correct")
        if questions_correct is None:
            questions_correct = max(0, questions_answered - questions_skipped)
        questions_correct = to_int(questions_correct, 0)

        total_errors = to_int(stats.get("total_errors"), 0)
        highest_streak = stats.get("highest_streak", stats.get("clean_streak"))
        highest_streak = to_int(highest_streak, 0)
        grace_seconds = to_int(stats.get("grace_period_seconds", 5), 5)

        ctk.CTkLabel(
            content,
            text="You've completed all questions!",
            font=message_font,
            text_color=self.COLORS["text_medium"],
            anchor="center",
        ).grid(row=0, column=0, pady=(0, row_pad))

        score_frame = ctk.CTkFrame(content, fg_color="transparent")
        score_frame.grid(row=1, column=0, pady=(0, row_pad))

        # Load star icon from SVG
        star_icon_size = max(int(32 * scale), 20)
        self.load_star_icon(star_icon_size)

        star_label = ctk.CTkLabel(
            score_frame,
            text="★" if self.star_icon is None else "",
            font=ctk.CTkFont(family="Segoe UI Symbol", size=star_icon_size),
            text_color=self.COLORS["warning_yellow"],
            image=self.star_icon,
        )
        star_label.grid(row=0, column=0, padx=(0, 12))

        ctk.CTkLabel(
            score_frame,
            text=str(self.final_score),
            font=score_font,
            text_color=self.COLORS["success_green"],
        ).grid(row=0, column=1)

        ctk.CTkLabel(
            score_frame,
            text="points",
            font=message_font,
            text_color=self.COLORS["text_medium"],
        ).grid(row=0, column=2, padx=(8, 0), sticky="s", pady=(0, 6))

        stats_card = ctk.CTkFrame(
            content,
            fg_color=self.COLORS["card_bg"],
            corner_radius=card_corner_r,
            border_width=1,
            border_color=self.COLORS["border_light"],
        )
        stats_card.grid(row=2, column=0, sticky="ew", pady=(0, pad // 2))
        stats_card.grid_columnconfigure(0, weight=1)

        rows_container = ctk.CTkFrame(stats_card, fg_color="transparent")
        rows_container.grid(row=0, column=0, sticky="nsew", padx=pad, pady=pad // 2)
        rows_container.grid_columnconfigure(0, weight=1)

        rows = [
            ("Total questions", str(total_questions), self.COLORS["primary_blue"]),
            ("Correct", str(questions_correct), self.COLORS["success_green"]),
            ("Skipped", str(questions_skipped), self.COLORS["warning_yellow"]),
            ("Errors", str(total_errors), self.COLORS["danger_red"]),
            ("Highest streak", str(highest_streak), self.COLORS["master_purple"]),
        ]

        self.animated_widgets.clear()
        bg_color = self.COLORS["bg_light"]
        self.widget_target_colors.clear()

        for i, (label_text, value_text, value_color) in enumerate(rows):
            row_frame = ctk.CTkFrame(rows_container, fg_color="transparent")
            row_frame.grid(row=i, column=0, sticky="ew", pady=row_pad // 2)
            row_frame.grid_columnconfigure(0, weight=1)
            row_frame.grid_columnconfigure(1, weight=0)

            label_widget = ctk.CTkLabel(
                row_frame,
                text=f"{label_text}:",
                font=label_font,
                text_color=bg_color,  # Start invisible
                anchor="w",
            )
            label_widget.grid(row=0, column=0, sticky="w")
            self.widget_target_colors[id(label_widget)] = self.COLORS["text_dark"]

            value_widget = ctk.CTkLabel(
                row_frame,
                text=value_text,
                font=value_font,
                text_color=bg_color,  # Start invisible
                anchor="e",
            )
            value_widget.grid(row=0, column=1, sticky="e", padx=(pad // 2, 0))
            self.widget_target_colors[id(value_widget)] = value_color

            self.animated_widgets.append((label_widget, value_widget))

        ctk.CTkLabel(
            content,
            text=(
                f"You get the first {grace_seconds} seconds free to read the clue. "
                "Time-based scoring starts after that."
            ),
            font=footnote_font,
            text_color=self.COLORS["text_medium"],
            justify="center",
            anchor="center",
            wraplength=int(width * 0.82),
        ).grid(row=3, column=0, pady=(0, pad // 2))

        button_container = ctk.CTkFrame(content, fg_color="transparent")
        button_container.grid(row=4, column=0, pady=(pad // 2, 0))

        previous_button = ctk.CTkButton(
            button_container,
            text="Previous Question",
            font=button_font,
            fg_color=self.COLORS["header_bg"] if self.has_previous else "#E8E8E8",
            hover_color=self.COLORS["header_bg"] if self.has_previous else "#E8E8E8",
            text_color=self.COLORS["text_white"] if self.has_previous else "#AAAAAA",
            command=self.handle_previous if self.has_previous else None,
            state="normal" if self.has_previous else "disabled",
            width=btn_w,
            height=btn_h,
            corner_radius=btn_r,
        )
        previous_button.grid(row=0, column=0, padx=(0, pad // 2))

        return_button = ctk.CTkButton(
            button_container,
            text="Return to Menu",
            font=button_font,
            width=btn_w,
            height=btn_h,
            fg_color=self.COLORS["primary_blue"],
            hover_color=self.COLORS["primary_hover"],
            text_color=self.COLORS["text_white"],
            corner_radius=btn_r,
            command=self.handle_close,
        )
        return_button.grid(row=0, column=1, padx=(pad // 2, 0))

        self.modal.protocol("WM_DELETE_WINDOW", self.handle_close)
        self.modal.bind("<Escape>", lambda e: self.handle_close())
        self.modal.bind("<Return>", lambda e: self.handle_close())

        self.safe_try(return_button.focus_set)
        self.start_fade_in_animation(bg_color)

    def load_star_icon(self, icon_size):
        star_svg_path = os.path.join(self.IMAGES_DIR, "star.svg")
        try:
            img = self.load_svg_image(star_svg_path, scale=self.SVG_RASTER_SCALE)
            if img:
                # Colorize the white star to yellow
                img = self.colorize_image(img, self.COLORS["warning_yellow"])
                self.star_icon = ctk.CTkImage(
                    light_image=img, dark_image=img, size=(icon_size, icon_size)
                )
        except (FileNotFoundError, OSError, ValueError):
            self.star_icon = None

    def colorize_image(self, img, hex_color):
        # Parse hex color
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)

        # Split into channels
        img_r, img_g, img_b, img_a = img.split()

        # Create new colored channels by blending original luminance with target color
        # Since the star is white, we just replace RGB with our color and keep alpha
        colored = Image.merge(
            "RGBA",
            (
                img_r.point(lambda x: int(x * r / 255)),
                img_g.point(lambda x: int(x * g / 255)),
                img_b.point(lambda x: int(x * b / 255)),
                img_a,
            ),
        )
        return colored

    def load_svg_image(self, svg_path, scale=1.0):
        try:
            svg_photo = TkSvgImage(file=str(svg_path), scale=scale)
            pil = ImageTk.getimage(svg_photo).convert("RGBA")
            return pil
        except (FileNotFoundError, ValueError) as e:
            print(f"Error loading SVG image '{svg_path}': {e}")
            return None

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

    def interpolate_color(self, start_hex, end_hex, progress):
        start_r = int(start_hex[1:3], 16)
        start_g = int(start_hex[3:5], 16)
        start_b = int(start_hex[5:7], 16)

        end_r = int(end_hex[1:3], 16)
        end_g = int(end_hex[3:5], 16)
        end_b = int(end_hex[5:7], 16)

        r = int(start_r + (end_r - start_r) * progress)
        g = int(start_g + (end_g - start_g) * progress)
        b = int(start_b + (end_b - start_b) * progress)

        return f"#{r:02x}{g:02x}{b:02x}"

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

    def handle_previous(self):
        self.close()
        if self.on_previous_callback:
            self.on_previous_callback()

    def handle_close(self):
        self.close()
        if self.on_close_callback:
            self.on_close_callback()

    def close(self):
        modal = self.modal
        for job in self.animation_jobs:
            if modal:
                self.safe_try(lambda j=job, m=modal: m.after_cancel(j))
        self.animation_jobs.clear()
        self.animated_widgets.clear()
        self.widget_target_colors.clear()

        modal_exists = False
        if modal:
            try:
                modal_exists = bool(modal.winfo_exists())
            except tk.TclError:
                modal_exists = False

        if modal_exists:
            self.safe_try(modal.grab_release)
            self.safe_try(modal.destroy)
        self.modal = None
        self.root = None

    def safe_try(self, func):
        try:
            func()
        except tk.TclError:
            pass


class QuestionSummaryModal:
    COLORS = {
        "bg_light": "#F5F7FA",
        "header_bg": "#202632",
        "text_white": "#FFFFFF",
        "text_dark": "#3A3F4B",
        "text_medium": "#7A7A7A",
        "primary_blue": "#005DFF",
        "primary_hover": "#003BB8",
        "success_green": "#00CFC5",
    }

    ANIMATION_DELAY_MS = 200  # Delay between each row appearing
    FADE_STEPS = 12  # Number of steps for fade animation
    FADE_STEP_MS = 30  # Milliseconds per fade step

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
    ):
        self.parent = parent
        self.correct_word = correct_word
        self.time_taken = time_taken
        self.points_awarded = points_awarded
        self.total_score = total_score
        self.on_next_callback = on_next_callback
        self.on_close_callback = on_close_callback
        self.on_previous_callback = on_previous_callback
        self.has_previous = has_previous
        self.modal = None
        self.root = None
        self.animation_jobs = []  # Track scheduled animations for cleanup
        self.animated_widgets = []  # Widgets to animate
        self.widget_target_colors = {}  # Store target colors for animation

    def show(self):
        if self.modal and self.modal.winfo_exists():
            self.safe_try(lambda: (self.modal.lift(), self.modal.focus_force()))
            return

        root = self.parent.winfo_toplevel() if self.parent else None

        if root and root.winfo_width() > 1 and root.winfo_height() > 1:
            width = int(root.winfo_width() * 0.38)
            height = int(root.winfo_height() * 0.38)
        else:
            width, height = 450, 280

        scale = min(width / 450, height / 340) * 0.75

        title_size = max(int(26 * scale), 16)
        label_size = max(int(15 * scale), 11)
        value_size = max(int(15 * scale), 11)
        button_size = max(int(16 * scale), 12)
        header_h = max(int(66 * scale), 44)
        btn_w = max(int(150 * scale), 100)
        btn_h = max(int(44 * scale), 32)
        btn_r = max(int(12 * scale), 8)
        pad = max(int(20 * scale), 12)
        row_pad = max(int(6 * scale), 4)
        corner_r = max(int(16 * scale), 12)
        border_w = max(int(3 * scale), 2)

        title_font = ctk.CTkFont(
            family="Poppins ExtraBold", size=title_size, weight="bold"
        )
        label_font = ctk.CTkFont(
            family="Poppins SemiBold", size=label_size, weight="bold"
        )
        value_font = ctk.CTkFont(
            family="Poppins SemiBold", size=value_size, weight="bold"
        )
        button_font = ctk.CTkFont(
            family="Poppins SemiBold", size=button_size, weight="bold"
        )

        self.root = root
        self.modal = ctk.CTkToplevel(root if root else self.parent)
        self.modal.after_cancel(
            self.modal.after(0, lambda: None)
        )  # Cancel CTk's icon update
        self.modal.iconphoto(False, tk.PhotoImage(width=1, height=1))  # Blank icon

        # Get scaling factor - geometry() applies this internally, so we divide
        try:
            scaling = ctk.ScalingTracker.get_window_scaling(root) if root else 1.0
        except (AttributeError, KeyError):
            scaling = 1.0

        # Calculate centered position in screen coordinates
        if root and root.winfo_width() > 1 and root.winfo_height() > 1:
            pos_x = root.winfo_rootx() + (root.winfo_width() - width) // 2
            pos_y = root.winfo_rooty() + (root.winfo_height() - height) // 2
        else:
            screen_w = self.modal.winfo_screenwidth()
            screen_h = self.modal.winfo_screenheight()
            pos_x = (screen_w - width) // 2
            pos_y = (screen_h - height) // 2

        # Divide by scaling since CTk's geometry() multiplies internally
        pos_x = int(pos_x / scaling)
        pos_y = int(pos_y / scaling)

        self.modal.geometry(f"{width}x{height}+{pos_x}+{pos_y}")

        # Disable the appear-on-top behavior that CTkToplevel does
        self.modal.attributes("-topmost", False)

        self.modal.title("Summary")

        if root:
            self.modal.transient(root)
            self.modal.grab_set()  # Use grab instead of disabling root
        self.modal.resizable(False, False)
        self.modal.configure(fg_color=self.COLORS["bg_light"])
        self.modal.grid_rowconfigure(0, weight=1)
        self.modal.grid_columnconfigure(0, weight=1)

        # Main container
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

        # Header
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

        ctk.CTkLabel(
            header,
            text="Summary",
            font=title_font,
            text_color=self.COLORS["text_white"],
            anchor="center",
        ).grid(row=0, column=0, sticky="nsew", padx=pad)

        # Content
        content_wrapper = ctk.CTkFrame(
            container,
            fg_color=self.COLORS["bg_light"],
            corner_radius=0,
        )
        content_wrapper.grid(row=1, column=0, sticky="nsew")
        content_wrapper.grid_rowconfigure(0, weight=1)
        content_wrapper.grid_columnconfigure(0, weight=1)

        content = ctk.CTkFrame(content_wrapper, fg_color="transparent")
        content.grid(row=0, column=0, sticky="")
        content.grid_columnconfigure(0, weight=1)

        rows = [
            ("Correct Word:", self.correct_word, self.COLORS["primary_blue"]),
            ("Time Taken:", f"{self.time_taken}s", self.COLORS["primary_blue"]),
            ("Points Awarded:", str(self.points_awarded), self.COLORS["primary_blue"]),
            ("Total Score:", str(self.total_score), self.COLORS["primary_blue"]),
        ]

        # Create rows with initial hidden state for animation
        self.animated_widgets.clear()
        bg_color = self.COLORS["bg_light"]
        self.widget_target_colors.clear()

        for i, (label_text, value_text, value_color) in enumerate(rows):
            label_widget = ctk.CTkLabel(
                content,
                text=label_text,
                font=label_font,
                text_color=bg_color,  # Start with same color as background (invisible)
                anchor="center",
            )
            label_widget.grid(row=i * 2, column=0, pady=(row_pad, 0))
            self.widget_target_colors[id(label_widget)] = self.COLORS["text_dark"]

            value_widget = ctk.CTkLabel(
                content,
                text=value_text,
                font=value_font,
                text_color=bg_color,  # Start invisible
                anchor="center",
            )
            value_widget.grid(row=i * 2 + 1, column=0, pady=(0, row_pad))
            self.widget_target_colors[id(value_widget)] = value_color

            self.animated_widgets.append((label_widget, value_widget))

        # Button container for side-by-side buttons
        button_container = ctk.CTkFrame(content, fg_color="transparent")
        button_container.grid(row=8, column=0, pady=(pad, 0))

        # Previous button (only enabled if has_previous)
        previous_button = ctk.CTkButton(
            button_container,
            text="Previous",
            font=button_font,
            fg_color=self.COLORS["header_bg"] if self.has_previous else "#E8E8E8",
            hover_color=self.COLORS["header_bg"] if self.has_previous else "#E8E8E8",
            text_color=self.COLORS["text_white"] if self.has_previous else "#AAAAAA",
            command=self.handle_previous if self.has_previous else None,
            state="normal" if self.has_previous else "disabled",
            width=btn_w,
            height=btn_h,
            corner_radius=btn_r,
        )
        previous_button.grid(row=0, column=0, padx=(0, pad // 2))

        close_button = ctk.CTkButton(
            button_container,
            text="Close",
            font=button_font,
            fg_color="#D0D6E0",
            hover_color="#B8C0D0",
            text_color=self.COLORS["text_white"],
            command=self.handle_close,
            width=btn_w,
            height=btn_h,
            corner_radius=btn_r,
        )
        close_button.grid(row=0, column=1, padx=(pad // 2, pad // 2))

        next_button = ctk.CTkButton(
            button_container,
            text="Next Question",
            font=button_font,
            fg_color=self.COLORS["primary_blue"],
            hover_color=self.COLORS["primary_hover"],
            text_color=self.COLORS["text_white"],
            command=self.handle_next,
            width=btn_w,
            height=btn_h,
            corner_radius=btn_r,
        )
        next_button.grid(row=0, column=2, padx=(pad // 2, 0))

        self.modal.protocol("WM_DELETE_WINDOW", self.handle_close)
        self.modal.bind("<Escape>", lambda e: self.handle_close())
        self.modal.bind("<Return>", lambda e: self.handle_next())

        # Start the fade-in animation
        self.start_fade_in_animation(bg_color)

    def start_fade_in_animation(self, bg_color):
        for row_index, (label_widget, value_widget) in enumerate(self.animated_widgets):
            delay = row_index * self.ANIMATION_DELAY_MS
            # Schedule fade-in for this row
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
            # Animation complete - set final colors
            self.safe_try(lambda: label_widget.configure(text_color=label_target))
            self.safe_try(lambda: value_widget.configure(text_color=value_target))
            return

        # Calculate interpolated colors
        progress = (step + 1) / self.FADE_STEPS
        label_color = self.interpolate_color(bg_color, label_target, progress)
        value_color = self.interpolate_color(bg_color, value_target, progress)

        self.safe_try(lambda: label_widget.configure(text_color=label_color))
        self.safe_try(lambda: value_widget.configure(text_color=value_color))

        # Schedule next step
        job = self.modal.after(
            self.FADE_STEP_MS,
            lambda: self.fade_in_row(label_widget, value_widget, bg_color, step + 1),
        )
        self.animation_jobs.append(job)

    def interpolate_color(self, start_hex, end_hex, progress):
        # Parse hex colors
        start_r = int(start_hex[1:3], 16)
        start_g = int(start_hex[3:5], 16)
        start_b = int(start_hex[5:7], 16)

        end_r = int(end_hex[1:3], 16)
        end_g = int(end_hex[3:5], 16)
        end_b = int(end_hex[5:7], 16)

        # Interpolate
        r = int(start_r + (end_r - start_r) * progress)
        g = int(start_g + (end_g - start_g) * progress)
        b = int(start_b + (end_b - start_b) * progress)

        return f"#{r:02x}{g:02x}{b:02x}"

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

    def close(self):
        # Cancel any pending animations
        for job in self.animation_jobs:
            self.safe_try(lambda j=job: self.modal.after_cancel(j))
        self.animation_jobs.clear()
        self.animated_widgets.clear()
        self.widget_target_colors.clear()

        if self.modal and self.modal.winfo_exists():
            self.safe_try(self.modal.grab_release)
            self.safe_try(self.modal.destroy)
        self.modal = None
        self.root = None

    def safe_try(self, func):
        try:
            func()
        except tk.TclError:
            pass


class SkipConfirmationModal:
    COLORS = {
        "bg_light": "#F5F7FA",
        "header_bg": "#202632",
        "text_white": "#FFFFFF",
        "text_dark": "#3A3F4B",
        "cancel_bg": "#D0D6E0",
        "cancel_hover": "#B8C0D0",
        "skip_bg": "#FF4F60",
        "skip_hover": "#CC3F4D",
    }

    def __init__(self, parent, on_skip_callback):
        self.parent = parent
        self.on_skip_callback = on_skip_callback
        self.modal = None
        self.root = None

    def show(self):
        if self.modal and self.modal.winfo_exists():
            self.safe_try(lambda: (self.modal.lift(), self.modal.focus_force()))
            return

        root = self.parent.winfo_toplevel() if self.parent else None

        # Calculate size first
        if root and root.winfo_width() > 1 and root.winfo_height() > 1:
            width = int(root.winfo_width() * 0.35)
            height = int(root.winfo_height() * 0.35)
        else:
            width, height = 400, 200

        # Scale factor based on modal size (base: 400x200), reduced by 0.6
        scale = min(width / 400, height / 200) * 0.6

        # Scale all sizes
        title_size = max(int(24 * scale), 16)
        body_size = max(int(16 * scale), 12)
        button_size = max(int(16 * scale), 12)
        header_h = max(int(72 * scale), 48)
        btn_w = max(int(120 * scale), 80)
        btn_h = max(int(44 * scale), 32)
        btn_r = max(int(12 * scale), 8)
        pad = max(int(24 * scale), 16)
        corner_r = max(int(16 * scale), 12)
        border_w = max(int(3 * scale), 2)

        title_font = ctk.CTkFont(
            family="Poppins ExtraBold", size=title_size, weight="bold"
        )
        body_font = ctk.CTkFont(
            family="Poppins SemiBold", size=body_size, weight="bold"
        )
        button_font = ctk.CTkFont(
            family="Poppins SemiBold", size=button_size, weight="bold"
        )

        self.root = root
        self.modal = ctk.CTkToplevel(root if root else self.parent)
        self.modal.after_cancel(
            self.modal.after(0, lambda: None)
        )  # Cancel CTk's icon update
        self.modal.iconphoto(False, tk.PhotoImage(width=1, height=1))  # Blank icon

        # Get scaling factor - geometry() applies this internally, so we divide
        try:
            scaling = ctk.ScalingTracker.get_window_scaling(root) if root else 1.0
        except (AttributeError, KeyError):
            scaling = 1.0

        # Calculate centered position in screen coordinates
        if root and root.winfo_width() > 1 and root.winfo_height() > 1:
            pos_x = root.winfo_rootx() + (root.winfo_width() - width) // 2
            pos_y = root.winfo_rooty() + (root.winfo_height() - height) // 2
        else:
            screen_width = self.modal.winfo_screenwidth()
            screen_height = self.modal.winfo_screenheight()
            pos_x = (screen_width - width) // 2
            pos_y = (screen_height - height) // 2

        # Divide by scaling since CTk's geometry() multiplies internally
        pos_x = int(pos_x / scaling)
        pos_y = int(pos_y / scaling)

        self.modal.geometry(f"{width}x{height}+{pos_x}+{pos_y}")

        # Disable the appear-on-top behavior that CTkToplevel does
        self.modal.attributes("-topmost", False)

        self.modal.title("Skip Question")

        if root:
            self.modal.transient(root)
            self.modal.grab_set()  # Use grab instead of disabling root
        self.modal.resizable(False, False)
        self.modal.configure(fg_color=self.COLORS["bg_light"])
        self.modal.grid_rowconfigure(0, weight=1)
        self.modal.grid_columnconfigure(0, weight=1)

        # Main container
        container = ctk.CTkFrame(
            self.modal,
            fg_color=self.COLORS["bg_light"],
            corner_radius=corner_r,
            border_width=border_w,
            border_color="#1D6CFF",
        )
        container.grid(row=0, column=0, sticky="nsew")
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(1, weight=1)

        # Header
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

        ctk.CTkLabel(
            header,
            text="Skip Question",
            font=title_font,
            text_color=self.COLORS["text_white"],
            anchor="center",
        ).grid(row=0, column=0, sticky="nsew", padx=pad)

        # Content
        content_wrapper = ctk.CTkFrame(
            container,
            fg_color=self.COLORS["bg_light"],
            corner_radius=0,
        )
        content_wrapper.grid(row=1, column=0, sticky="nsew")
        content_wrapper.grid_rowconfigure(0, weight=1)
        content_wrapper.grid_rowconfigure(1, weight=0)
        content_wrapper.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            content_wrapper,
            text="Are you sure you want to skip the question? No points will be awarded.",
            font=body_font,
            text_color=self.COLORS["text_dark"],
            justify="center",
            anchor="center",
            wraplength=int(width * 0.8),
        ).grid(row=0, column=0, sticky="nsew", pady=pad, padx=pad)

        buttons_frame = ctk.CTkFrame(content_wrapper, fg_color="transparent")
        buttons_frame.grid(row=1, column=0, pady=(0, pad))

        ctk.CTkButton(
            buttons_frame,
            text="Cancel",
            font=button_font,
            fg_color=self.COLORS["cancel_bg"],
            hover_color=self.COLORS["cancel_hover"],
            text_color=self.COLORS["text_white"],
            command=self.close,
            width=btn_w,
            height=btn_h,
            corner_radius=btn_r,
        ).grid(row=0, column=0, padx=(0, pad))

        ctk.CTkButton(
            buttons_frame,
            text="Skip",
            font=button_font,
            fg_color=self.COLORS["skip_bg"],
            hover_color=self.COLORS["skip_hover"],
            text_color=self.COLORS["text_white"],
            command=self.handle_skip,
            width=btn_w,
            height=btn_h,
            corner_radius=btn_r,
        ).grid(row=0, column=1, padx=(pad, 0))

        self.modal.protocol("WM_DELETE_WINDOW", self.close)
        self.modal.bind("<Escape>", lambda e: self.close())

    def handle_skip(self):
        self.close()
        if self.on_skip_callback:
            self.on_skip_callback()

    def close(self):
        if self.modal and self.modal.winfo_exists():
            self.safe_try(self.modal.grab_release)
            self.safe_try(self.modal.destroy)
        self.modal = None
        self.root = None

    def safe_try(self, func):
        try:
            func()
        except tk.TclError:
            pass


class GameScreen:
    BASE_DIMENSIONS = (1280, 720)
    BASE_FONT_SIZES = {
        "timer": 24,
        "score": 28,
        "definition": 16,
        "keyboard": 18,
        "answer_box": 20,
        "button": 20,
        "header_label": 14,
        "feedback": 14,
    }
    SCALE_LIMITS = (0.50, 1.60)
    RESIZE_DELAY = 80
    SVG_RASTER_SCALE = 2.0
    AUDIO_ICON_BASE_SIZE = 36
    AUDIO_ICON_MIN_SIZE = 28
    AUDIO_ICON_MAX_SIZE = 48
    DELETE_ICON_BASE_SIZE = 26

    BASE_IMAGE_SIZE = 180
    IMAGE_MIN_SIZE = 100
    IMAGE_MAX_SIZE = 280

    BASE_KEY_SIZE = 44
    KEY_MIN_SIZE = 32
    KEY_MAX_SIZE = 60

    BASE_ANSWER_BOX_SIZE = 40
    ANSWER_BOX_MIN_SIZE = 28
    ANSWER_BOX_MAX_SIZE = 56

    COLORS = {
        "primary_blue": "#005DFF",
        "primary_hover": "#003BB8",
        "success_green": "#00CFC5",
        "success_hover": "#009B94",
        "warning_yellow": "#FFC553",
        "warning_hover": "#CC9A42",
        "danger_red": "#FF4F60",
        "danger_hover": "#CC3F4D",
        "text_dark": "#202632",
        "text_medium": "#3A3F4B",
        "text_light": "#7A7A7A",
        "bg_light": "#F5F7FA",
        "bg_card": "#FFFFFF",
        "border_light": "#E2E7F3",
        "border_medium": "#D3DBEA",
        "header_bg": "#202632",
        "header_hover": "#273246",
        "key_bg": "#E8ECF2",
        "key_hover": "#D0D6E0",
        "key_pressed": "#B8C0D0",
        "answer_box_empty": "#E2E7F3",
        "answer_box_filled": "#D0D6E0",
        "feedback_correct": "#00CFC5",
        "feedback_incorrect": "#FF4F60",
    }

    KEYBOARD_LAYOUT = [
        ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
        ["A", "S", "D", "F", "G", "H", "J", "K", "L"],
        ["Z", "X", "C", "V", "B", "N", "M", "⌫"],
    ]

    def __init__(self, parent, on_return_callback=None, tts_service=None):
        self.parent = parent
        self.on_return_callback = on_return_callback

        self.current_question = None
        self.questions = []
        self.available_questions = []
        self.score = 0
        self.current_answer = ""
        self.timer_seconds = 0
        self.audio_enabled = True
        self.timer_running = False
        self.timer_job = None
        self.questions_answered = 0
        self.game_completed = False
        self.completion_modal = None

        # Scoring system (initialized after questions are loaded)
        self.scoring_system = None

        # Wildcard manager
        self.wildcard_manager = WildcardManager()

        # Per-question tracking for scoring
        self.question_timer = 0  # Seconds spent on current question
        self.question_mistakes = 0  # Wrong attempts on current question

        self.resize_job = None
        self.main = None
        self.header_frame = None
        self.back_button = None
        self.back_arrow_icon = None
        self.timer_label = None
        self.score_label = None
        self.audio_toggle_btn = None
        self.question_container = None
        self.image_frame = None
        self.image_label = None
        self.definition_label = None
        self.answer_boxes_frame = None
        self.answer_box_labels = []
        self.keyboard_frame = None
        self.keyboard_buttons = []
        self.delete_button = None
        self.action_buttons_frame = None
        self.skip_button = None
        self.check_button = None
        self.current_image = None
        self.audio_icon_on = None
        self.audio_icon_off = None
        self.clock_icon = None
        self.star_icon = None
        self.delete_icon = None
        self.timer_icon_label = None
        self.star_icon_label = None
        self.wildcards_frame = None
        self.wildcard_x2_btn = None
        self.wildcard_hint_btn = None
        self.wildcard_freeze_btn = None
        self.info_icon = None
        self.info_icon_label = None
        self.feedback_label = None
        self.feedback_animation_job = None
        self.skip_modal = None
        self.summary_modal = None
        self.processing_correct_answer = False  # Prevent multiple submissions
        self.awaiting_modal_decision = False  # True when modal closed but not proceeded
        self.stored_modal_data = None  # Store modal data for re-showing

        # Question history for navigating to previous questions
        self.question_history = []  # List of completed question states
        self.viewing_history_index = (
            -1
        )  # -1 means viewing current question, >= 0 means viewing history

        self.images_dir = os.path.join("recursos", "imagenes")
        self.audio_dir = os.path.join("recursos", "audio")
        self.questions_path = os.path.join("datos", "preguntas.json")

        self.tts = tts_service or TTSService(self.audio_dir)

        # Map for physical key -> virtual keyboard button (for visual feedback)
        self.key_button_map = {}
        # Track currently pressed key for visual feedback
        self.physical_key_pressed = None
        self.key_feedback_job = None

        self.create_fonts()

        self.load_questions()
        self.build_ui()

        self.parent.bind("<Configure>", self.on_resize)
        # Bind physical keyboard events
        self.bind_physical_keyboard()
        self.apply_responsive()

        self.load_random_question()
        self.start_timer()

    def create_fonts(self):
        self.timer_font = ctk.CTkFont(
            family="Poppins SemiBold",
            size=self.BASE_FONT_SIZES["timer"],
            weight="bold",
        )
        self.score_font = ctk.CTkFont(
            family="Poppins ExtraBold",
            size=self.BASE_FONT_SIZES["score"],
            weight="bold",
        )
        self.definition_font = ctk.CTkFont(
            family="Open Sans Regular",
            size=self.BASE_FONT_SIZES["definition"],
        )
        self.keyboard_font = ctk.CTkFont(
            family="Poppins SemiBold",
            size=self.BASE_FONT_SIZES["keyboard"],
            weight="bold",
        )
        self.answer_box_font = ctk.CTkFont(
            family="Poppins ExtraBold",
            size=self.BASE_FONT_SIZES["answer_box"],
            weight="bold",
        )
        self.button_font = ctk.CTkFont(
            family="Poppins SemiBold",
            size=self.BASE_FONT_SIZES["button"],
        )
        self.header_button_font = ctk.CTkFont(
            family="Poppins SemiBold",
            size=20,
            weight="bold",
        )
        self.header_label_font = ctk.CTkFont(
            family="Poppins SemiBold",
            size=self.BASE_FONT_SIZES["header_label"],
        )
        self.feedback_font = ctk.CTkFont(
            family="Poppins SemiBold",
            size=self.BASE_FONT_SIZES["feedback"],
            weight="bold",
        )

    def load_questions(self):
        try:
            with open(self.questions_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.questions = data.get("questions", [])
                # Initialize available questions pool (copy of all questions)
                self.available_questions = list(self.questions)
                # Initialize the scoring system with the total number of questions
                self.scoring_system = ScoringSystem(len(self.questions))
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading questions: {e}")
            self.questions = []
            self.available_questions = []
            self.scoring_system = ScoringSystem(1)  # Fallback

    def build_ui(self):

        for widget in self.parent.winfo_children():
            widget.destroy()

        self.parent.grid_rowconfigure(0, weight=1)
        self.parent.grid_columnconfigure(0, weight=1)

        self.main = ctk.CTkFrame(self.parent, fg_color="transparent")
        self.main.grid(row=0, column=0, sticky="nsew")

        self.main.grid_rowconfigure(0, weight=0)
        self.main.grid_rowconfigure(1, weight=1)
        self.main.grid_rowconfigure(2, weight=0)
        self.main.grid_rowconfigure(3, weight=0)
        self.main.grid_columnconfigure(0, weight=1)

        self.build_header()
        self.build_question_container()
        self.build_keyboard()
        self.build_action_buttons()

    def build_header(self):
        self.header_frame = ctk.CTkFrame(
            self.main,
            fg_color=self.COLORS["header_bg"],
            height=60,
            corner_radius=0,
        )
        self.header_frame.grid(row=0, column=0, sticky="ew")
        self.header_frame.grid_propagate(False)

        self.header_frame.grid_columnconfigure(0, weight=1)
        self.header_frame.grid_columnconfigure(1, weight=0)
        self.header_frame.grid_columnconfigure(2, weight=1)
        self.header_frame.grid_rowconfigure(0, weight=1)

        left_container = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        left_container.grid(row=0, column=0, sticky="w", padx=(0, 0))

        self.load_header_icons()

        self.back_button = ctk.CTkButton(
            left_container,
            text="Menu",
            image=self.back_arrow_icon,
            compound="left",
            anchor="w",
            font=self.header_button_font,
            width=96,
            height=40,
            fg_color="transparent",
            hover_color=self.COLORS["header_hover"],
            text_color="white",
            corner_radius=8,
            command=self.return_to_menu,
        )
        self.back_button.grid(row=0, column=0, padx=(0, 16))

        timer_container = ctk.CTkFrame(left_container, fg_color="transparent")
        timer_container.grid(row=0, column=1, padx=(8, 0))

        self.timer_icon_label = ctk.CTkLabel(
            timer_container,
            text="",
            image=self.clock_icon,
        )
        self.timer_icon_label.grid(row=0, column=0, padx=(0, 8))

        self.timer_label = ctk.CTkLabel(
            timer_container,
            text="00:00",
            font=self.timer_font,
            text_color="white",
        )
        self.timer_label.grid(row=0, column=1)

        score_container = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        score_container.grid(row=0, column=1)

        self.star_icon_label = ctk.CTkLabel(
            score_container,
            text="",
            image=self.star_icon,
        )
        self.star_icon_label.grid(row=0, column=0, padx=(0, 8))

        self.score_label = ctk.CTkLabel(
            score_container,
            text="0",
            font=self.score_font,
            text_color="white",
        )
        self.score_label.grid(row=0, column=1)

        audio_container = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        audio_container.grid(row=0, column=2, sticky="e", padx=(0, 24))

        self.load_audio_icons()

        self.audio_toggle_btn = ctk.CTkButton(
            audio_container,
            text="",
            image=self.audio_icon_on,
            font=self.timer_font,
            width=48,
            height=40,
            fg_color="transparent",
            hover_color=self.COLORS["header_hover"],
            text_color="white",
            corner_radius=8,
            command=self.toggle_audio,
        )
        self.audio_toggle_btn.grid(row=0, column=0)
        self.update_audio_button_icon()

    def load_header_icons(self):

        arrow_svg_path = os.path.join(self.images_dir, "arrow.svg")
        try:
            img = self.load_svg_image(arrow_svg_path, scale=self.SVG_RASTER_SCALE)
            if img:
                self.back_arrow_icon = ctk.CTkImage(
                    light_image=img, dark_image=img, size=(20, 20)
                )
        except (FileNotFoundError, OSError, ValueError):
            self.back_arrow_icon = None

        clock_svg_path = os.path.join(self.images_dir, "clock.svg")
        try:
            img = self.load_svg_image(clock_svg_path, scale=self.SVG_RASTER_SCALE)
            if img:
                self.clock_icon = ctk.CTkImage(
                    light_image=img, dark_image=img, size=(24, 24)
                )
        except (FileNotFoundError, OSError, ValueError):
            self.clock_icon = None

        star_svg_path = os.path.join(self.images_dir, "star.svg")
        try:
            img = self.load_svg_image(star_svg_path, scale=self.SVG_RASTER_SCALE)
            if img:
                self.star_icon = ctk.CTkImage(
                    light_image=img, dark_image=img, size=(24, 24)
                )
        except (FileNotFoundError, OSError, ValueError):
            self.star_icon = None

    def load_audio_icons(self):
        self.audio_icon_on = None
        self.audio_icon_off = None

        icon_size = self.calculate_audio_icon_size(scale=1.0)

        icon_specs = [
            ("audio_icon_on", "volume-white.svg"),
            ("audio_icon_off", "volume-mute.svg"),
        ]

        for attr, filename in icon_specs:
            svg_path = os.path.join(self.images_dir, filename)
            try:
                img = self.load_svg_image(svg_path, scale=self.SVG_RASTER_SCALE)
                if img:
                    setattr(
                        self,
                        attr,
                        ctk.CTkImage(
                            light_image=img,
                            dark_image=img,
                            size=(icon_size, icon_size),
                        ),
                    )
            except (FileNotFoundError, OSError, ValueError):
                setattr(self, attr, None)

    def calculate_audio_icon_size(self, scale, back_height=None):
        base_scaled = self.AUDIO_ICON_BASE_SIZE * scale
        size_targets = [
            base_scaled,
            self.timer_font.cget("size"),
            self.score_font.cget("size"),
        ]
        if back_height:
            size_targets.append(back_height * 0.85)
        target_size = max(size_targets)
        return int(
            max(
                self.AUDIO_ICON_MIN_SIZE,
                min(self.AUDIO_ICON_MAX_SIZE, target_size),
            )
        )

    def update_audio_icon_size(self, icon_size, back_height=None, corner_radius=None):
        for icon in (self.audio_icon_on, self.audio_icon_off):
            if icon:
                icon.configure(size=(icon_size, icon_size))

        if not self.audio_toggle_btn:
            return

        current_width = int(self.audio_toggle_btn.cget("width"))
        current_height = int(self.audio_toggle_btn.cget("height"))

        audio_height = max(current_height, int(icon_size + 8), int(back_height or 0))
        audio_width = max(current_width, int(icon_size + 12), audio_height)

        kwargs = {
            "width": audio_width,
            "height": audio_height,
        }
        if corner_radius is not None:
            kwargs["corner_radius"] = corner_radius

        self.audio_toggle_btn.configure(**kwargs)

    def update_audio_button_icon(self):
        if not self.audio_toggle_btn:
            return

        icon = self.audio_icon_on if self.audio_enabled else self.audio_icon_off
        if icon:
            self.audio_toggle_btn.configure(image=icon, text="")
        else:
            fallback_text = "On" if self.audio_enabled else "Off"
            self.audio_toggle_btn.configure(image=None, text=fallback_text)

    def load_info_icon(self):
        info_svg_path = os.path.join(self.images_dir, "info.svg")
        try:
            img = self.load_svg_image(info_svg_path, scale=self.SVG_RASTER_SCALE)
            if img:
                self.info_icon = ctk.CTkImage(
                    light_image=img, dark_image=img, size=(24, 24)
                )
        except (FileNotFoundError, OSError, ValueError):
            self.info_icon = None

    def load_delete_icon(self):
        delete_svg_path = os.path.join(self.images_dir, "delete.svg")
        try:
            img = self.load_svg_image(delete_svg_path, scale=self.SVG_RASTER_SCALE)
            if img:
                icon_size = self.calculate_delete_icon_size(self.BASE_KEY_SIZE)
                self.delete_icon = ctk.CTkImage(
                    light_image=img,
                    dark_image=img,
                    size=(icon_size, icon_size),
                )
        except (FileNotFoundError, OSError, ValueError):
            self.delete_icon = None

    def calculate_delete_icon_size(self, key_size):
        scale_factor = self.DELETE_ICON_BASE_SIZE / self.BASE_KEY_SIZE
        target_size = key_size * scale_factor
        return int(max(16, min(40, target_size)))

    def update_delete_icon_size(self, key_size):
        if not self.delete_icon:
            return
        icon_size = self.calculate_delete_icon_size(key_size)
        self.delete_icon.configure(size=(icon_size, icon_size))

    def build_question_container(self):

        self.question_container = ctk.CTkFrame(
            self.main,
            fg_color=self.COLORS["bg_card"],
            corner_radius=20,
            border_width=2,
            border_color=self.COLORS["border_light"],
        )
        self.question_container.grid(row=1, column=0, sticky="nsew", padx=40, pady=20)

        # Two columns: left for the card content, right for wildcards
        self.question_container.grid_columnconfigure(0, weight=1)
        self.question_container.grid_columnconfigure(1, weight=0)
        self.question_container.grid_rowconfigure(0, weight=0)
        self.question_container.grid_rowconfigure(1, weight=1)
        self.question_container.grid_rowconfigure(2, weight=0)
        self.question_container.grid_rowconfigure(3, weight=0)

        # Use scaled size from the start to prevent small-to-large flash
        initial_image_size = self.get_scaled_image_size()

        # Frame expands horizontally with column, keeping label centered inside
        self.image_frame = ctk.CTkFrame(
            self.question_container,
            fg_color="transparent",
            height=initial_image_size,
        )
        self.image_frame.grid(row=0, column=0, sticky="ew", pady=(20, 10))
        # Center content in frame
        self.image_frame.grid_rowconfigure(0, weight=1)
        self.image_frame.grid_columnconfigure(0, weight=1)

        self.image_label = ctk.CTkLabel(
            self.image_frame,
            text="",
            fg_color=self.COLORS["bg_light"],
            corner_radius=16,
            width=initial_image_size,
            height=initial_image_size,
        )
        self.image_label.grid(row=0, column=0)

        definition_frame = ctk.CTkFrame(self.question_container, fg_color="transparent")
        definition_frame.grid(row=1, column=0, sticky="nsew", padx=30, pady=10)
        definition_frame.grid_columnconfigure(0, weight=1)
        definition_frame.grid_rowconfigure(0, weight=1)

        self.load_info_icon()

        definition_inner = ctk.CTkFrame(definition_frame, fg_color="transparent")
        definition_inner.grid(row=0, column=0, sticky="")

        self.info_icon_label = ctk.CTkLabel(
            definition_inner,
            text="",
            image=self.info_icon,
        )
        self.info_icon_label.grid(row=0, column=0, sticky="n", padx=(0, 8), pady=(2, 0))

        self.definition_label = ctk.CTkLabel(
            definition_inner,
            text="Loading question...",
            font=self.definition_font,
            text_color=self.COLORS["text_medium"],
            wraplength=600,
            justify="left",
            anchor="w",
        )
        self.definition_label.grid(row=0, column=1, sticky="w")

        # Use scaled size from the start to prevent small-to-large flash
        initial_box_size = self.get_scaled_box_size()
        # Pre-allocate frame for ~10 character word to prevent resize on first question
        initial_frame_width = 10 * (initial_box_size + 6)
        initial_frame_height = initial_box_size + 4

        self.answer_boxes_frame = ctk.CTkFrame(
            self.question_container,
            fg_color="transparent",
            width=initial_frame_width,
            height=initial_frame_height,
        )
        self.answer_boxes_frame.grid(row=2, column=0, pady=(10, 8))
        # Prevent frame from collapsing when children are hidden/shown
        self.answer_boxes_frame.grid_propagate(False)

        # Feedback label (Correct / Incorrect)
        self.feedback_label = ctk.CTkLabel(
            self.question_container,
            text="",
            font=self.feedback_font,
            text_color=self.COLORS["feedback_correct"],
        )
        self.feedback_label.grid(row=3, column=0, pady=(0, 16))

        self.build_wildcards_panel()

    def build_wildcards_panel(self):

        self.wildcards_frame = ctk.CTkFrame(
            self.question_container,
            fg_color="transparent",
        )
        self.wildcards_frame.grid(
            row=0, column=1, rowspan=4, sticky="ns", padx=(0, 24), pady=24
        )

        self.wildcards_frame.grid_rowconfigure(0, weight=1)
        self.wildcards_frame.grid_rowconfigure(4, weight=1)

        wildcard_size = 56
        wildcard_font_size = 18

        self.wildcard_x2_btn = ctk.CTkButton(
            self.wildcards_frame,
            text="X2",
            font=ctk.CTkFont(
                family="Poppins ExtraBold", size=wildcard_font_size, weight="bold"
            ),
            width=wildcard_size,
            height=wildcard_size,
            corner_radius=wildcard_size,
            fg_color="#FFC553",
            hover_color="#E5B04A",
            text_color="white",
            command=self.on_wildcard_x2,
        )
        self.wildcard_x2_btn.grid(row=1, column=0, pady=8)

        self.wildcard_hint_btn = ctk.CTkButton(
            self.wildcards_frame,
            text="A",
            font=ctk.CTkFont(
                family="Poppins ExtraBold", size=wildcard_font_size, weight="bold"
            ),
            width=wildcard_size,
            height=wildcard_size,
            corner_radius=wildcard_size,
            fg_color="#00CFC5",
            hover_color="#00B5AD",
            text_color="white",
            command=self.on_wildcard_hint,
        )
        self.wildcard_hint_btn.grid(row=2, column=0, pady=8)

        self.wildcard_freeze_btn = ctk.CTkButton(
            self.wildcards_frame,
            text="❄",
            font=ctk.CTkFont(family="Segoe UI Emoji", size=wildcard_font_size),
            width=wildcard_size,
            height=wildcard_size,
            corner_radius=wildcard_size,
            fg_color="#005DFF",
            hover_color="#0048CC",
            text_color="white",
            command=self.on_wildcard_freeze,
        )
        self.wildcard_freeze_btn.grid(row=3, column=0, pady=8)

    def on_wildcard_x2(self):
        if not self.current_question:
            return

        # Block when awaiting modal or viewing history
        if self.awaiting_modal_decision or self.viewing_history_index >= 0:
            return

        # Stack another multiplier
        self.wildcard_manager.activate_double_points()
        multiplier = self.wildcard_manager.get_points_multiplier()

        # Update button to show current multiplier
        self.wildcard_x2_btn.configure(
            text=f"X{multiplier}", fg_color="#4CAF50"  # Active green
        )

    def on_wildcard_hint(self):
        if not self.current_question:
            return

        # Block when awaiting modal or viewing history
        if self.awaiting_modal_decision or self.viewing_history_index >= 0:
            return

        title = self.current_question.get("title", "")
        clean_title = title.replace(" ", "").upper()

        # Get a random unrevealed position
        result = self.wildcard_manager.get_random_unrevealed_position(
            self.current_answer, clean_title
        )

        if result is None:
            # All letters already revealed or correct
            return

        position, letter = result

        # Insert the letter into the current answer
        # Convert current answer to a list, pad to full length if needed
        answer_list = list(self.current_answer.upper())

        # Pad with empty spaces if current answer is shorter than position
        while len(answer_list) <= position:
            answer_list.append(" ")

        # Set the revealed letter
        answer_list[position] = letter

        # Convert back to string (remove trailing spaces but keep internal ones as letters)
        self.current_answer = "".join(answer_list).rstrip()

        # Update the visual display
        self.update_answer_boxes_with_reveal(position)

    def on_wildcard_freeze(self):
        if not self.current_question:
            return

        # Block when awaiting modal or viewing history
        if self.awaiting_modal_decision or self.viewing_history_index >= 0:
            return

        # Already frozen - cannot be toggled (one-time per question)
        if self.wildcard_manager.is_timer_frozen():
            return

        # Freeze - stop timer (one-way, stays frozen until next question)
        self.wildcard_manager.activate_freeze()
        self.wildcard_freeze_btn.configure(fg_color="#4CAF50")  # Active green
        self.stop_timer()

    def reset_wildcard_button_colors(self):
        if self.wildcard_x2_btn:
            self.wildcard_x2_btn.configure(
                text="X2", fg_color="#FFC553"
            )  # Default yellow
        if self.wildcard_hint_btn:
            self.wildcard_hint_btn.configure(fg_color="#00CFC5")  # Default teal
        if self.wildcard_freeze_btn:
            self.wildcard_freeze_btn.configure(fg_color="#005DFF")  # Default blue

    def build_keyboard(self):
        self.keyboard_frame = ctk.CTkFrame(
            self.main,
            fg_color="transparent",
        )
        self.keyboard_frame.grid(row=2, column=0, pady=(0, 16), padx=256, sticky="ew")
        self.keyboard_frame.grid_columnconfigure(0, weight=1)

        self.keyboard_buttons.clear()
        self.key_button_map.clear()  # Clear the key->button mapping
        self.delete_button = None
        self.load_delete_icon()

        for row_idx, row_keys in enumerate(self.KEYBOARD_LAYOUT):
            row_frame = ctk.CTkFrame(self.keyboard_frame, fg_color="transparent")
            row_frame.grid(row=row_idx, column=0, pady=4, sticky="ew")
            row_frame.grid_columnconfigure(0, weight=1)
            row_frame.grid_columnconfigure(2, weight=1)

            inner_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            inner_frame.grid(row=0, column=1)

            for col_idx, key in enumerate(row_keys):

                if key == "⌫":
                    width = int(self.BASE_KEY_SIZE * 1.8)
                    fg_color = self.COLORS["danger_red"]
                    hover_color = self.COLORS["danger_hover"]
                    text_color = "white"
                    btn_image = self.delete_icon
                    btn_text = "" if btn_image else key
                else:
                    width = self.BASE_KEY_SIZE
                    fg_color = self.COLORS["key_bg"]
                    hover_color = self.COLORS["key_hover"]
                    text_color = self.COLORS["text_dark"]
                    btn_image = None
                    btn_text = key

                btn = ctk.CTkButton(
                    inner_frame,
                    text=btn_text,
                    image=btn_image,
                    font=self.keyboard_font,
                    width=width,
                    height=self.BASE_KEY_SIZE,
                    fg_color=fg_color,
                    hover_color=hover_color,
                    text_color=text_color,
                    border_width=2,
                    border_color=self.COLORS["header_bg"],
                    corner_radius=8,
                    command=lambda k=key: self.on_key_press(k),
                )
                btn.grid(row=0, column=col_idx, padx=12)
                self.keyboard_buttons.append(btn)

                # Store key->button mapping for physical keyboard feedback
                self.key_button_map[key] = btn

                if key == "⌫":
                    self.delete_button = btn

    def build_action_buttons(self):
        self.action_buttons_frame = ctk.CTkFrame(self.main, fg_color="transparent")
        self.action_buttons_frame.grid(row=3, column=0, pady=(0, 24))

        self.skip_button = ctk.CTkButton(
            self.action_buttons_frame,
            text="Skip",
            font=self.button_font,
            width=140,
            height=48,
            fg_color=self.COLORS["bg_light"],
            hover_color=self.COLORS["border_medium"],
            text_color="black",
            border_width=2,
            border_color="black",
            corner_radius=12,
            command=self.on_skip,
        )
        self.skip_button.grid(row=0, column=0, padx=16)

        self.check_button = ctk.CTkButton(
            self.action_buttons_frame,
            text="Check",
            font=self.button_font,
            width=140,
            height=48,
            fg_color="#005DFF",
            hover_color="#003BB8",
            text_color="white",
            corner_radius=12,
            command=self.on_check,
        )
        self.check_button.grid(row=0, column=1, padx=16)

    def create_answer_boxes(self, word_length):
        # Reuse existing boxes to prevent layout bounce during question transitions
        current_count = len(self.answer_box_labels)
        box_size = self.get_scaled_box_size()

        # Create additional boxes if needed
        for i in range(current_count, word_length):
            box = ctk.CTkLabel(
                self.answer_boxes_frame,
                text="",
                font=self.answer_box_font,
                width=box_size,
                height=box_size,
                fg_color=self.COLORS["answer_box_empty"],
                corner_radius=8,
                text_color=self.COLORS["text_dark"],
            )
            self.answer_box_labels.append(box)

        # Show boxes needed for current word and reset their state
        revealed_positions = self.wildcard_manager.get_revealed_positions()
        for i in range(word_length):
            box = self.answer_box_labels[i]
            # Check if this position has content (from current answer or revealed)
            if i < len(self.current_answer) and self.current_answer[i].strip():
                if i in revealed_positions:
                    box.configure(
                        text=self.current_answer[i],
                        fg_color=self.COLORS["success_green"],
                        width=box_size,
                        height=box_size,
                    )
                else:
                    box.configure(
                        text=self.current_answer[i],
                        fg_color=self.COLORS["answer_box_filled"],
                        width=box_size,
                        height=box_size,
                    )
            else:
                box.configure(
                    text="",
                    fg_color=self.COLORS["answer_box_empty"],
                    width=box_size,
                    height=box_size,
                )
            box.grid(row=0, column=i, padx=3)

        # Hide excess boxes (don't destroy - keep for reuse)
        for i in range(word_length, len(self.answer_box_labels)):
            self.answer_box_labels[i].grid_remove()

        # Update frame size to fit current boxes
        frame_width = max(box_size, word_length * (box_size + 6))  # 6 = 2*padx(3)
        frame_height = box_size + 4  # Small padding
        self.answer_boxes_frame.configure(width=frame_width, height=frame_height)

    def load_random_question(self):
        self.tts.stop()
        self.hide_feedback()
        self.processing_correct_answer = False  # Reset for new question

        # Reset wildcards for new question
        self.wildcard_manager.reset_for_new_question()
        self.reset_wildcard_button_colors()

        # Check if there are no questions loaded at all
        if not self.questions:
            self.definition_label.configure(text="No questions available!")
            return

        # Check if all questions have been answered/skipped
        if not self.available_questions:
            self.handle_game_completion()
            return

        # Select and remove a random question from available pool
        self.current_question = random.choice(self.available_questions)
        self.available_questions.remove(self.current_question)

        self.current_answer = ""

        # Reset per-question tracking for scoring
        self.question_timer = 0
        self.question_mistakes = 0

        # Reset timer display for new question
        self.timer_label.configure(text="00:00")

        definition = self.current_question.get("definition", "No definition")
        self.definition_label.configure(text=definition)

        title = self.current_question.get("title", "")

        clean_title = title.replace(" ", "")
        self.create_answer_boxes(len(clean_title))

        self.load_question_image()

        if self.audio_enabled and definition and definition != "No definition":
            self.tts.speak(definition)

    def load_question_image(self):
        if not self.current_question:
            return

        image_path = self.current_question.get("image", "")
        if not image_path:
            self.image_label.configure(image=None, text="No Image")
            return

        try:

            if not os.path.isabs(image_path):
                image_path = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)), image_path
                )

            if os.path.exists(image_path):
                pil_image = Image.open(image_path).convert("RGBA")

                # Use current scaled size to fit image within container
                max_size = self.get_scaled_image_size()

                width, height = pil_image.size
                img_scale = min(max_size / width, max_size / height)
                new_width = int(width * img_scale)
                new_height = int(height * img_scale)

                self.current_image = ctk.CTkImage(
                    light_image=pil_image,
                    dark_image=pil_image,
                    size=(new_width, new_height),
                )
                # Only update image content, not dimensions (frame handles size)
                self.image_label.configure(
                    image=self.current_image,
                    text="",
                )
            else:
                self.image_label.configure(image=None, text="Image not found")
        except (FileNotFoundError, OSError, ValueError) as e:
            print(f"Error loading image: {e}")
            self.image_label.configure(image=None, text="Error loading image")

    def on_key_press(self, key):
        if not self.current_question:
            return

        # Block input when awaiting modal decision
        if self.awaiting_modal_decision:
            return

        title = self.current_question.get("title", "")
        clean_title = title.replace(" ", "")
        max_length = len(clean_title)
        revealed_positions = self.wildcard_manager.get_revealed_positions()

        if key == "⌫":
            # Delete: remove the last user-typed character (not revealed ones)
            if self.current_answer:
                # Convert to list padded to current length
                answer_list = list(self.current_answer)

                # Find the last non-revealed, non-empty position to clear
                deleted = False
                for i in range(len(answer_list) - 1, -1, -1):
                    # Skip revealed positions - they cannot be deleted
                    if i in revealed_positions:
                        continue
                    # Skip empty positions
                    if not answer_list[i] or answer_list[i] == " ":
                        continue
                    # Found a user-typed character - clear it (don't pop to keep indices stable)
                    answer_list[i] = ""
                    deleted = True
                    break

                if deleted:
                    # Trim trailing empty characters while preserving revealed ones
                    while answer_list:
                        last_idx = len(answer_list) - 1
                        if last_idx in revealed_positions:
                            break  # Don't trim revealed positions
                        if answer_list[last_idx] and answer_list[last_idx] != " ":
                            break  # Don't trim non-empty characters
                        answer_list.pop()
                    self.current_answer = "".join(answer_list)
        else:
            # Add letter: find the next empty position (not revealed)
            answer_list = list(self.current_answer)
            # Pad to max length to check all positions
            while len(answer_list) < max_length:
                answer_list.append("")

            # Find first empty non-revealed position
            inserted = False
            for i in range(max_length):
                if i not in revealed_positions and (
                    not answer_list[i] or answer_list[i] == " "
                ):
                    answer_list[i] = key
                    inserted = True
                    break

            if inserted:
                # Remove trailing empty strings
                while answer_list and (answer_list[-1] == "" or answer_list[-1] == " "):
                    answer_list.pop()
                self.current_answer = "".join(answer_list)

        self.update_answer_boxes()

    def update_answer_boxes(self):
        revealed_positions = self.wildcard_manager.get_revealed_positions()
        for i, box in enumerate(self.answer_box_labels):
            if i < len(self.current_answer) and self.current_answer[i].strip():
                # Check if this position was revealed by wildcard
                if i in revealed_positions:
                    box.configure(
                        text=self.current_answer[i],
                        fg_color=self.COLORS["success_green"],  # Highlighted color
                    )
                else:
                    box.configure(
                        text=self.current_answer[i],
                        fg_color=self.COLORS["answer_box_filled"],
                    )
            else:
                box.configure(
                    text="",
                    fg_color=self.COLORS["answer_box_empty"],
                )

    def update_answer_boxes_with_reveal(self, revealed_position):
        revealed_positions = self.wildcard_manager.get_revealed_positions()

        for i, box in enumerate(self.answer_box_labels):
            if i < len(self.current_answer) and self.current_answer[i].strip():
                if i in revealed_positions:
                    # Revealed letter - use green highlight
                    box.configure(
                        text=self.current_answer[i],
                        fg_color=self.COLORS["success_green"],
                    )
                else:
                    box.configure(
                        text=self.current_answer[i],
                        fg_color=self.COLORS["answer_box_filled"],
                    )
            else:
                box.configure(
                    text="",
                    fg_color=self.COLORS["answer_box_empty"],
                )

        # Animate the newly revealed box with a brief flash
        if revealed_position < len(self.answer_box_labels):
            self.animate_reveal_flash(revealed_position)

    def animate_reveal_flash(self, position):
        if position >= len(self.answer_box_labels):
            return

        box = self.answer_box_labels[position]

        # Flash sequence: bright -> normal green
        def flash_step_1():
            try:
                box.configure(fg_color="#00FFE5")  # Bright cyan flash
            except tk.TclError:
                pass

        def flash_step_2():
            try:
                box.configure(fg_color=self.COLORS["success_green"])
            except tk.TclError:
                pass

        flash_step_1()
        self.parent.after(150, flash_step_2)

    def toggle_audio(self):
        self.audio_enabled = not self.audio_enabled
        self.update_audio_button_icon()
        if self.audio_enabled:
            if self.current_question:
                definition = self.current_question.get("definition", "").strip()
                if definition:
                    self.tts.speak(definition)
        else:
            self.tts.stop()

    def on_skip(self):
        if not self.current_question:
            return

        # Prevent skipping during completion processing or while in paused/history states
        if (
            self.processing_correct_answer
            or self.awaiting_modal_decision
            or self.viewing_history_index >= 0
        ):
            return

        if self.skip_modal is None:
            self.skip_modal = SkipConfirmationModal(self.parent, self.do_skip)
        self.skip_modal.show()

    def do_skip(self):
        if not self.current_question:
            return

        # Freeze timer/audio for the completed question (skip behaves like a completed attempt)
        self.stop_timer()
        self.tts.stop()

        title = self.current_question.get("title", "")

        points_earned = 0

        # Process skip through scoring system (0 points)
        if self.scoring_system:
            self.scoring_system.process_skip(mistakes=self.question_mistakes)
            self.questions_answered = self.scoring_system.questions_answered
            self.score = self.scoring_system.total_score
        else:
            self.questions_answered += 1

        # Keep UI score in sync (even though skip awards 0, total may be managed by scoring_system)
        self.score_label.configure(text=str(self.score))

        # Store complete question state for history (so skipped questions can be revisited)
        self.stored_modal_data = {
            "correct_word": title,
            "time_taken": self.question_timer,
            "points_awarded": points_earned,
            "total_score": self.score,
            # Visual state for restoring when viewing history
            "question": self.current_question,
            "answer": self.current_answer,
            "current_image": self.current_image,
            "was_skipped": True,
        }

        self.show_feedback(skipped=True)
        self.show_summary_modal_for_state(self.stored_modal_data)

    def handle_game_completion(self):
        if self.game_completed:
            return

        self.game_completed = True
        self.stop_timer()
        self.tts.stop()

        # Clear the current question display
        self.current_question = None
        self.definition_label.configure(text="Game Complete!")

        # Show the completion modal
        session_stats = (
            self.scoring_system.get_session_stats() if self.scoring_system else None
        )
        self.completion_modal = GameCompletionModal(
            parent=self.parent,
            final_score=self.score,
            total_questions=len(self.questions),
            session_stats=session_stats,
            on_previous_callback=self.on_completion_previous,
            has_previous=bool(self.question_history),
            on_close_callback=self.return_to_menu,
        )
        self.completion_modal.show()

    def on_check(self):
        if not self.current_question:
            return

        # If viewing history, just re-show the modal for that history item
        if self.viewing_history_index >= 0:
            history_item = self.question_history[self.viewing_history_index]
            self.show_summary_modal_for_state(
                history_item, review_mode=self.game_completed
            )
            return

        # If awaiting modal decision on current question, just re-show the modal
        if self.awaiting_modal_decision and self.stored_modal_data:
            self.show_summary_modal_for_state(self.stored_modal_data)
            return

        # Prevent multiple submissions while processing a correct answer
        if self.processing_correct_answer:
            return

        title = self.current_question.get("title", "")
        clean_title = title.replace(" ", "").upper()
        user_answer = self.current_answer.upper()

        if user_answer == clean_title:
            self.processing_correct_answer = True  # Block further submissions
            self.stop_timer()  # Stop the timer immediately
            self.tts.stop()  # Interrupt TTS playback
            self.show_feedback(correct=True)

            points_earned = 0
            if self.scoring_system:
                result = self.scoring_system.process_correct_answer(
                    time_seconds=self.question_timer,
                    mistakes=self.question_mistakes,
                )
                points_earned = result.points_earned

                # Apply double points multiplier if active
                multiplier = self.wildcard_manager.get_points_multiplier()
                if multiplier > 1:
                    bonus_points = points_earned * (multiplier - 1)
                    points_earned = points_earned * multiplier
                    # Add bonus to total score (result.points_earned already added)
                    self.scoring_system.total_score += bonus_points

                self.score = self.scoring_system.total_score
                self.questions_answered = self.scoring_system.questions_answered
            else:
                multiplier = self.wildcard_manager.get_points_multiplier()
                points_earned = 100 * multiplier
                self.score += points_earned
                self.questions_answered += 1

            self.score_label.configure(text=str(self.score))

            # Store complete question state for history
            self.stored_modal_data = {
                "correct_word": title,
                "time_taken": self.question_timer,
                "points_awarded": points_earned,
                "total_score": self.score,
                # Visual state for restoring when viewing history
                "question": self.current_question,
                "answer": self.current_answer,
                "current_image": self.current_image,
                "was_skipped": False,
            }

            self.parent.after(
                600, lambda: self.show_summary_modal_for_state(self.stored_modal_data)
            )
        else:
            self.question_mistakes += 1
            self.show_feedback(correct=False)

    def show_summary_modal_for_state(self, state_data, review_mode=False):
        # Determine if there's a previous question to go to
        if self.viewing_history_index >= 0:
            # Viewing history - can go previous if not at index 0
            has_previous = self.viewing_history_index > 0
        else:
            # Viewing current - can go previous if there's any history
            has_previous = len(self.question_history) > 0

        if review_mode:
            on_next_callback = self.on_review_modal_next
            on_close_callback = self.on_review_modal_close
            on_previous_callback = self.on_review_modal_previous
        else:
            on_next_callback = self.on_modal_next
            on_close_callback = self.on_modal_close
            on_previous_callback = self.on_modal_previous

        self.summary_modal = QuestionSummaryModal(
            parent=self.parent,
            correct_word=state_data["correct_word"],
            time_taken=state_data["time_taken"],
            points_awarded=state_data["points_awarded"],
            total_score=state_data["total_score"],
            on_next_callback=on_next_callback,
            on_close_callback=on_close_callback,
            on_previous_callback=on_previous_callback,
            has_previous=has_previous,
        )
        self.summary_modal.show()

    def show_completion_modal_again(self):
        if self.completion_modal is None:
            session_stats = (
                self.scoring_system.get_session_stats() if self.scoring_system else None
            )
            self.completion_modal = GameCompletionModal(
                parent=self.parent,
                final_score=self.score,
                total_questions=len(self.questions),
                session_stats=session_stats,
                on_previous_callback=self.on_completion_previous,
                has_previous=bool(self.question_history),
                on_close_callback=self.return_to_menu,
            )

        self.completion_modal.show()

    def on_completion_previous(self):
        if not self.question_history:
            self.show_completion_modal_again()
            return

        self.viewing_history_index = len(self.question_history) - 1
        self.load_history_state(self.viewing_history_index)

    def on_review_modal_next(self):
        if (
            self.viewing_history_index >= 0
            and self.viewing_history_index < len(self.question_history) - 1
        ):
            self.viewing_history_index += 1
            self.load_history_state(self.viewing_history_index)
            return

        self.viewing_history_index = -1
        self.show_completion_modal_again()

    def on_review_modal_close(self):
        # Close should behave like the normal "paused" close: keep the current
        # history question on screen and allow "Check" to open the modal again.
        self.on_modal_close()

    def on_review_modal_previous(self):
        if self.viewing_history_index > 0:
            self.viewing_history_index -= 1
            self.load_history_state(self.viewing_history_index)

    def on_modal_next(self):
        if self.viewing_history_index >= 0:
            # Currently viewing history
            if self.viewing_history_index < len(self.question_history) - 1:
                # Go to next history item
                self.viewing_history_index += 1
                self.load_history_state(self.viewing_history_index)
            else:
                # At end of history, return to current question
                self.return_to_current_question()
        else:
            # Viewing current question - save to history and load next
            if self.stored_modal_data:
                self.question_history.append(self.stored_modal_data)
            self.awaiting_modal_decision = False
            self.stored_modal_data = None
            self.set_buttons_enabled(True)
            self.load_random_question()
            if not self.game_completed and self.current_question:
                self.start_timer()

    def on_modal_close(self):
        self.awaiting_modal_decision = True
        self.set_buttons_enabled(False)

    def on_modal_previous(self):
        if self.viewing_history_index >= 0:
            # Already viewing history, go to previous item
            if self.viewing_history_index > 0:
                self.viewing_history_index -= 1
                self.load_history_state(self.viewing_history_index)
        else:
            # Currently on current question, go to last item in history
            # (don't add current to history yet - that happens on Next)
            if self.question_history:
                self.viewing_history_index = len(self.question_history) - 1
                self.load_history_state(self.viewing_history_index)

    def load_history_state(self, index):
        if index < 0 or index >= len(self.question_history):
            return

        state = self.question_history[index]
        self.viewing_history_index = index

        # Restore the question data
        self.current_question = state["question"]
        self.current_answer = state["answer"]

        # Update the visual display
        definition = self.current_question.get("definition", "No definition")
        self.definition_label.configure(text=definition)

        title = self.current_question.get("title", "")
        clean_title = title.replace(" ", "")
        self.create_answer_boxes(len(clean_title))
        self.update_answer_boxes()

        # Restore the timer display
        minutes = state["time_taken"] // 60
        seconds = state["time_taken"] % 60
        self.timer_label.configure(text=f"{minutes:02d}:{seconds:02d}")

        # Restore the score display
        self.score_label.configure(text=str(state["total_score"]))

        # Restore the image
        self.load_question_image()

        # Show feedback based on how the question was completed
        if state.get("was_skipped", False):
            self.show_feedback(skipped=True)
        else:
            self.show_feedback(correct=True)

        # Ensure buttons are disabled
        self.set_buttons_enabled(False)
        self.awaiting_modal_decision = True

    def return_to_current_question(self):
        # Return to the *paused* current question state (the one that opened the modal),
        # not the next random game question.
        self.viewing_history_index = -1

        if not self.stored_modal_data:
            # Nothing to restore; fall back to enabling gameplay.
            self.awaiting_modal_decision = False
            self.set_buttons_enabled(True)
            return

        state = self.stored_modal_data

        # Restore the current question snapshot that was saved when answering correctly.
        self.current_question = state["question"]
        self.current_answer = state["answer"]

        definition = self.current_question.get("definition", "No definition")
        self.definition_label.configure(text=definition)

        title = self.current_question.get("title", "")
        clean_title = title.replace(" ", "")
        self.create_answer_boxes(len(clean_title))
        self.update_answer_boxes()

        minutes = state["time_taken"] // 60
        seconds = state["time_taken"] % 60
        self.timer_label.configure(text=f"{minutes:02d}:{seconds:02d}")

        self.score_label.configure(text=str(state["total_score"]))

        self.load_question_image()
        if state.get("was_skipped", False):
            self.show_feedback(skipped=True)
        else:
            self.show_feedback(correct=True)

        self.set_buttons_enabled(False)
        self.awaiting_modal_decision = True

    def set_buttons_enabled(self, enabled):
        state = "normal" if enabled else "disabled"

        # Disable keyboard buttons
        for btn in self.key_button_map.values():
            try:
                btn.configure(state=state)
            except (tk.TclError, AttributeError):
                pass

        # Disable delete button
        if self.delete_button:
            try:
                self.delete_button.configure(state=state)
            except (tk.TclError, AttributeError):
                pass

        # Disable skip button
        if self.skip_button:
            try:
                self.skip_button.configure(state=state)
            except (tk.TclError, AttributeError):
                pass

        # Disable audio toggle
        if self.audio_toggle_btn:
            try:
                self.audio_toggle_btn.configure(state=state)
            except (tk.TclError, AttributeError):
                pass

        # Disable wildcard buttons
        if self.wildcard_x2_btn:
            try:
                self.wildcard_x2_btn.configure(state=state)
            except (tk.TclError, AttributeError):
                pass
        if self.wildcard_hint_btn:
            try:
                self.wildcard_hint_btn.configure(state=state)
            except (tk.TclError, AttributeError):
                pass
        if self.wildcard_freeze_btn:
            try:
                self.wildcard_freeze_btn.configure(state=state)
            except (tk.TclError, AttributeError):
                pass

    def show_feedback(self, correct=True, skipped=False):
        # Cancel any ongoing animation
        if self.feedback_animation_job:
            self.parent.after_cancel(self.feedback_animation_job)
            self.feedback_animation_job = None

        if skipped:
            text = "⏭ Skipped"
            color = self.COLORS.get("warning_yellow", "#FFC553")
        elif correct:
            text = "✓ Correct!"
            color = self.COLORS["feedback_correct"]
        else:
            text = "✗ Incorrect - Try Again"
            color = self.COLORS["feedback_incorrect"]

        self.feedback_label.configure(text=text, text_color=color)

        # Simple fade-in animation using opacity simulation
        self.animate_feedback_fade_in(0)

    def animate_feedback_fade_in(self, step):
        total_steps = 5
        if step > total_steps:
            return

        # Simulate fade by interpolating color from background to target
        # Since CustomTkinter doesn't support true opacity, we use color interpolation
        if step == 0:
            # Start with lighter/faded color
            self.feedback_label.configure(text_color="#F5F7FA")  # Match background
        else:
            # Get target color from current feedback type
            current_text = self.feedback_label.cget("text")
            if "Skipped" in current_text:
                target_color = self.COLORS.get("warning_yellow", "#FFC553")
            elif "Correct" in current_text:
                target_color = self.COLORS["feedback_correct"]
            else:
                target_color = self.COLORS["feedback_incorrect"]

            # Interpolate color
            faded_color = self.interpolate_color(
                "#F5F7FA", target_color, step / total_steps
            )
            self.feedback_label.configure(text_color=faded_color)

        if step < total_steps:
            self.feedback_animation_job = self.parent.after(
                40, lambda: self.animate_feedback_fade_in(step + 1)
            )

    def interpolate_color(self, color1, color2, factor):
        # Parse hex colors
        r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
        r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)

        # Interpolate
        r = int(r1 + (r2 - r1) * factor)
        g = int(g1 + (g2 - g1) * factor)
        b = int(b1 + (b2 - b1) * factor)

        return f"#{r:02x}{g:02x}{b:02x}"

    def hide_feedback(self):
        if self.feedback_animation_job:
            self.parent.after_cancel(self.feedback_animation_job)
            self.feedback_animation_job = None
        self.feedback_label.configure(text="")

    def start_timer(self):
        self.timer_running = True
        if self.timer_job:
            try:
                self.parent.after_cancel(self.timer_job)
            except tk.TclError:
                pass
            self.timer_job = None

        # Start counting after 1 second so the timer shows 00:00 initially
        self.timer_job = self.parent.after(1000, self.update_timer)

    def stop_timer(self):
        self.timer_running = False
        if self.timer_job:
            self.parent.after_cancel(self.timer_job)
            self.timer_job = None

    def update_timer(self):
        if not self.timer_running:
            return

        # Track per-question time for scoring
        self.question_timer += 1

        # Display per-question timer
        minutes = self.question_timer // 60
        seconds = self.question_timer % 60
        self.timer_label.configure(text=f"{minutes:02d}:{seconds:02d}")

        self.timer_job = self.parent.after(1000, self.update_timer)

    def get_current_scale(self):
        width = max(self.parent.winfo_width(), 1)
        height = max(self.parent.winfo_height(), 1)
        scale = min(width / self.BASE_DIMENSIONS[0], height / self.BASE_DIMENSIONS[1])
        return max(self.SCALE_LIMITS[0], min(self.SCALE_LIMITS[1], scale))

    def get_scaled_image_size(self, scale=None):
        if scale is None:
            scale = self.get_current_scale()
        return int(
            max(
                self.IMAGE_MIN_SIZE,
                min(self.IMAGE_MAX_SIZE, self.BASE_IMAGE_SIZE * scale),
            )
        )

    def get_scaled_box_size(self, scale=None):
        if scale is None:
            scale = self.get_current_scale()
        return int(
            max(
                self.ANSWER_BOX_MIN_SIZE,
                min(self.ANSWER_BOX_MAX_SIZE, self.BASE_ANSWER_BOX_SIZE * scale),
            )
        )

    def on_resize(self, event):
        if event.widget is not self.parent:
            return

        if self.resize_job:
            self.parent.after_cancel(self.resize_job)
        self.resize_job = self.parent.after(self.RESIZE_DELAY, self.apply_responsive)

    def apply_responsive(self):
        width = max(self.parent.winfo_width(), 1)
        height = max(self.parent.winfo_height(), 1)

        scale = min(width / self.BASE_DIMENSIONS[0], height / self.BASE_DIMENSIONS[1])
        scale = max(self.SCALE_LIMITS[0], min(self.SCALE_LIMITS[1], scale))

        self.timer_font.configure(
            size=int(max(14, self.BASE_FONT_SIZES["timer"] * scale))
        )
        self.score_font.configure(
            size=int(max(16, self.BASE_FONT_SIZES["score"] * scale))
        )
        self.definition_font.configure(
            size=int(max(12, self.BASE_FONT_SIZES["definition"] * scale))
        )
        self.keyboard_font.configure(
            size=int(max(12, self.BASE_FONT_SIZES["keyboard"] * scale))
        )
        self.answer_box_font.configure(
            size=int(max(14, self.BASE_FONT_SIZES["answer_box"] * scale))
        )
        self.button_font.configure(
            size=int(max(12, self.BASE_FONT_SIZES["button"] * scale))
        )
        self.header_button_font.configure(size=int(max(12, min(32, 20 * scale))))
        self.header_label_font.configure(
            size=int(max(10, self.BASE_FONT_SIZES["header_label"] * scale))
        )
        self.feedback_font.configure(
            size=int(max(11, self.BASE_FONT_SIZES["feedback"] * scale))
        )

        def clamp_scaled(base, min_value, max_value):
            return int(max(min_value, min(max_value, base * scale)))

        pad_top = clamp_scaled(28, 12, 64)
        pad_bottom = clamp_scaled(32, 14, 72)
        pad_left = clamp_scaled(24, 10, 60)
        pad_right = clamp_scaled(16, 8, 48)
        back_width = clamp_scaled(96, 70, 170)
        back_height = clamp_scaled(40, 30, 64)
        back_corner = clamp_scaled(8, 6, 16)

        header_height = max(
            back_height + pad_top + pad_bottom, int(max(48, 60 * scale))
        )
        self.header_frame.configure(height=header_height)

        if self.back_button:
            self.back_button.grid_configure(
                padx=(pad_left, pad_right), pady=(pad_top, pad_bottom)
            )
            self.back_button.configure(
                width=back_width, height=back_height, corner_radius=back_corner
            )

        audio_icon_size = self.calculate_audio_icon_size(scale, back_height)
        self.update_audio_icon_size(audio_icon_size, back_height, back_corner)

        image_size = self.get_scaled_image_size(scale)
        # Update frame height (width handled by sticky="ew") and label size
        self.image_frame.configure(height=image_size)
        self.image_label.configure(width=image_size, height=image_size)

        if self.current_image and self.current_question:
            self.load_question_image()

        wrap_length = int(max(300, min(800, 600 * scale)))
        self.definition_label.configure(wraplength=wrap_length)

        box_size = self.get_scaled_box_size(scale)
        # Count visible boxes (those that are grid-managed)
        visible_boxes = [b for b in self.answer_box_labels if b.winfo_manager()]
        for box in self.answer_box_labels:
            box.configure(width=box_size, height=box_size)
        # Update frame size to match visible boxes
        if visible_boxes:
            frame_width = len(visible_boxes) * (box_size + 6)
            frame_height = box_size + 4
            self.answer_boxes_frame.configure(width=frame_width, height=frame_height)

        key_size = int(
            max(
                self.KEY_MIN_SIZE,
                min(self.KEY_MAX_SIZE, self.BASE_KEY_SIZE * scale),
            )
        )
        for btn in self.keyboard_buttons:
            is_delete_key = btn is self.delete_button
            if is_delete_key:
                btn.configure(width=int(key_size * 1.8), height=key_size)
                self.update_delete_icon_size(key_size)
            else:
                btn.configure(width=key_size, height=key_size)

        button_width = int(max(100, 140 * scale))
        button_height = int(max(36, 48 * scale))
        self.skip_button.configure(width=button_width, height=button_height)
        self.check_button.configure(width=button_width, height=button_height)

        container_padx = int(max(20, 40 * scale))
        container_pady = int(max(12, 20 * scale))
        self.question_container.grid_configure(padx=container_padx, pady=container_pady)

        keyboard_padx = int(max(128, 256 * scale))
        self.keyboard_frame.grid_configure(padx=keyboard_padx)

        self.resize_job = None

    def load_svg_image(self, svg_path, scale=1.0):
        try:
            svg_photo = TkSvgImage(file=str(svg_path), scale=scale)
            pil = ImageTk.getimage(svg_photo).convert("RGBA")
            return pil
        except (FileNotFoundError, ValueError) as e:
            print(f"Error loading SVG image '{svg_path}': {e}")
            return None

    def return_to_menu(self):
        self.cleanup()
        if self.on_return_callback:
            self.on_return_callback()

    def cleanup(self):
        self.stop_timer()
        self.tts.stop()
        if self.feedback_animation_job:
            self.parent.after_cancel(self.feedback_animation_job)
            self.feedback_animation_job = None
        if self.key_feedback_job:
            self.parent.after_cancel(self.key_feedback_job)
            self.key_feedback_job = None
        if self.completion_modal:
            self.completion_modal.close()
            self.completion_modal = None
        if self.summary_modal:
            self.summary_modal.close()
            self.summary_modal = None
        if self.skip_modal:
            self.skip_modal.close()
            self.skip_modal = None
        self.parent.unbind("<Configure>")
        self.unbind_physical_keyboard()

    # Physical Keyboard Support

    def bind_physical_keyboard(self):
        root = self.parent.winfo_toplevel()
        # Bind key press and release for visual feedback
        root.bind("<KeyPress>", self.on_physical_key_press)
        root.bind("<KeyRelease>", self.on_physical_key_release)

    def unbind_physical_keyboard(self):
        try:
            root = self.parent.winfo_toplevel()
            root.unbind("<KeyPress>")
            root.unbind("<KeyRelease>")
        except tk.TclError:
            pass  # Ignore errors during cleanup

    def on_physical_key_press(self, event):
        # Don't process if a modal is open
        if self.is_modal_open():
            return

        # Get the key character (uppercase for consistency)
        key_char = event.char.upper() if event.char else ""
        key_sym = event.keysym

        # Handle Enter -> trigger Check button (always allowed, even when awaiting)
        if key_sym == "Return":
            self.simulate_button_press(self.check_button)
            self.on_check()
            return

        # Block other inputs when awaiting modal decision
        if self.awaiting_modal_decision:
            return

        # Handle letter keys (A-Z)
        if key_char.isalpha() and len(key_char) == 1:
            self.show_key_feedback(key_char)
            self.on_key_press(key_char)
            return

        # Handle BackSpace -> maps to ⌫
        if key_sym == "BackSpace":
            self.show_key_feedback("⌫")
            self.on_key_press("⌫")
            return

        # Handle Escape -> trigger Skip (open confirmation modal)
        if key_sym == "Escape":
            self.simulate_button_press(self.skip_button)
            self.on_skip()
            return

    def on_physical_key_release(self, event):
        key_char = event.char.upper() if event.char else ""
        key_sym = event.keysym

        # Reset visual feedback for letter keys
        if key_char.isalpha() and len(key_char) == 1:
            self.reset_key_feedback(key_char)
            return

        # Reset visual feedback for BackSpace
        if key_sym == "BackSpace":
            self.reset_key_feedback("⌫")
            return

    def show_key_feedback(self, key):
        if key in self.key_button_map:
            btn = self.key_button_map[key]
            # Store original color and apply pressed color
            if key == "⌫":
                btn.configure(fg_color=self.COLORS["danger_hover"])
            else:
                btn.configure(fg_color=self.COLORS["key_pressed"])

    def reset_key_feedback(self, key):
        if key in self.key_button_map:
            btn = self.key_button_map[key]
            # Restore original color
            if key == "⌫":
                btn.configure(fg_color=self.COLORS["danger_red"])
            else:
                btn.configure(fg_color=self.COLORS["key_bg"])

    def simulate_button_press(self, button):
        if button is None:
            return

        original_color = button.cget("fg_color")
        hover_color = button.cget("hover_color")

        # Show pressed state
        button.configure(fg_color=hover_color)

        # Reset after a brief delay
        def reset():
            try:
                if button.winfo_exists():
                    button.configure(fg_color=original_color)
            except tk.TclError:
                pass

        self.parent.after(100, reset)

    def is_modal_open(self):
        if self.completion_modal and self.completion_modal.modal:
            try:
                if self.completion_modal.modal.winfo_exists():
                    return True
            except tk.TclError:
                pass

        if self.summary_modal and self.summary_modal.modal:
            try:
                if self.summary_modal.modal.winfo_exists():
                    return True
            except tk.TclError:
                pass

        if self.skip_modal and self.skip_modal.modal:
            try:
                if self.skip_modal.modal.winfo_exists():
                    return True
            except tk.TclError:
                pass

        return False

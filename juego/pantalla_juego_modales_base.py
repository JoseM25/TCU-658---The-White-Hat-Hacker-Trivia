import tkinter as tk

import customtkinter as ctk
from PIL import ImageTk
from tksvg import SvgImage as TkSvgImage

from juego.pantalla_juego_config import GAME_COLORS, MODAL_ANIMATION
from juego.rutas_app import get_resource_images_dir


class ModalBase:
    COLORS = GAME_COLORS
    IMAGES_DIR = get_resource_images_dir()
    SVG_RASTER_SCALE = 2.0
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
        self.resizable_widgets = {}
        self.resizable_fonts = {}
        self.closing = (
            False  # Bandera para prevenir nuevos trabajos de animación durante cierre
        )

    def get_window_scaling(self, root):
        try:
            scaling = ctk.ScalingTracker.get_window_scaling(root) if root else 1.0
        except (AttributeError, KeyError, ValueError, tk.TclError):
            scaling = 1.0
        if not scaling or scaling <= 0:
            return 1.0
        return scaling

    def get_logical_window_size(self, root, fallback=(1280, 720)):
        if not root:
            return fallback
        scaling = self.get_window_scaling(root)
        try:
            width = max(int(round(root.winfo_width() / scaling)), 1)
            height = max(int(round(root.winfo_height() / scaling)), 1)
        except tk.TclError:
            return fallback
        return width, height

    def calculate_scale_factor(self, root):
        if not root or not root.winfo_exists():
            return 1.0
        width, height = self.get_logical_window_size(root, (0, 0))
        if width <= 1 or height <= 1:
            return 1.0
        base_scale = min(width / 1280, height / 720)
        min_dim = min(width, height)
        # Penalizaciones de escalado más graduales para pantallas pequeñas
        # Asegura que los modales ajusten bien en 1080p (altura=1080) y menor
        if min_dim <= 720:
            base_scale *= 0.55
        elif min_dim <= 800:
            base_scale *= 0.70
        elif min_dim <= 900:
            base_scale *= 0.82
        elif min_dim <= 1080:
            # Penalización suave para pantallas 1080p para asegurar que el contenido ajuste
            base_scale *= 0.92
        return max(0.4, min(1.4, base_scale))

    def create_modal(self, width, height, title):
        root = self.parent.winfo_toplevel() if self.parent else None
        self.root = root
        self.modal = ctk.CTkToplevel(root if root else self.parent)
        self.modal.after_cancel(self.modal.after(0, lambda: None))
        self.modal.iconphoto(False, tk.PhotoImage(width=1, height=1))
        scaling = self.get_window_scaling(root or self.modal)
        scaled_width = max(int(round(width * scaling)), 1)
        scaled_height = max(int(round(height * scaling)), 1)
        if root and root.winfo_width() > 1 and root.winfo_height() > 1:
            pos_x = root.winfo_rootx() + (root.winfo_width() - scaled_width) // 2
            pos_y = root.winfo_rooty() + (root.winfo_height() - scaled_height) // 2
        else:
            pos_x = (self.modal.winfo_screenwidth() - scaled_width) // 2
            pos_y = (self.modal.winfo_screenheight() - scaled_height) // 2
        pos_x, pos_y = int(pos_x), int(pos_y)
        self.modal.geometry(f"{width}x{height}+{pos_x}+{pos_y}")
        self.modal.attributes("-topmost", False)
        self.modal.title(title)
        if root:
            self.modal.transient(root)
            self.modal.grab_set()
        self.modal.resizable(False, False)
        # Re-center modal after widgets are rendered
        self.modal.update_idletasks()
        final_w = self.modal.winfo_width()
        final_h = self.modal.winfo_height()
        if root and root.winfo_width() > 1 and root.winfo_height() > 1:
            pos_x = root.winfo_rootx() + (root.winfo_width() - final_w) // 2
            pos_y = root.winfo_rooty() + (root.winfo_height() - final_h) // 2
        else:
            pos_x = (self.modal.winfo_screenwidth() - final_w) // 2
            pos_y = (self.modal.winfo_screenheight() - final_h) // 2
        pos_x, pos_y = int(pos_x), int(pos_y)
        self.modal.geometry(f"+{pos_x}+{pos_y}")
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

    def make_font(self, family, size, weight=None):
        return (
            ctk.CTkFont(family=family, size=size, weight=weight)
            if weight
            else ctk.CTkFont(family=family, size=size)
        )

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
        sr, sg, sb = (
            int(start_hex[1:3], 16),
            int(start_hex[3:5], 16),
            int(start_hex[5:7], 16),
        )
        er, eg, eb = int(end_hex[1:3], 16), int(end_hex[3:5], 16), int(end_hex[5:7], 16)
        r, g, b = (
            int(sr + (er - sr) * progress),
            int(sg + (eg - sg) * progress),
            int(sb + (eb - sb) * progress),
        )
        return f"#{r:02x}{g:02x}{b:02x}"

    def start_fade_in_animation(self, bg_color):
        for i, (lw, vw) in enumerate(self.animated_widgets):
            delay = i * self.ANIMATION_DELAY_MS
            job = self.modal.after(
                delay, lambda l=lw, v=vw, bg=bg_color: self.fade_in_row(l, v, bg, 0)
            )
            self.animation_jobs.append(job)

    def fade_in_row(self, label_widget, value_widget, bg_color, step):
        # Verificar bandera de cierre para prevenir programación durante cierre
        if self.closing:
            return
        if not self.modal or not self.modal.winfo_exists():
            return
        label_target = self.widget_target_colors.get(id(label_widget))
        value_target = self.widget_target_colors.get(id(value_widget))
        if step >= self.FADE_STEPS:
            self.safe_try(lambda: label_widget.configure(text_color=label_target))
            self.safe_try(lambda: value_widget.configure(text_color=value_target))
            return
        progress = (step + 1) / self.FADE_STEPS
        self.safe_try(
            lambda: label_widget.configure(
                text_color=self.interpolate_color(bg_color, label_target, progress)
            )
        )
        self.safe_try(
            lambda: value_widget.configure(
                text_color=self.interpolate_color(bg_color, value_target, progress)
            )
        )
        # Verificar bandera de cierre de nuevo antes de programar
        if self.closing:
            return
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
        # Establecer bandera de cierre primero para prevenir nuevos trabajos de animación
        self.closing = True
        modal = self.modal
        # Copiar la lista para evitar modificación durante iteración
        jobs_to_cancel = list(self.animation_jobs)
        self.animation_jobs.clear()
        for job in jobs_to_cancel:
            if modal:
                self.safe_try(lambda j=job, m=modal: m.after_cancel(j))
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
        self.closing = False  # Reiniciar para posible reutilización

    def safe_try(self, func):
        try:
            func()
        except tk.TclError:
            pass

    def resize(self, scale):
        self.current_scale = scale

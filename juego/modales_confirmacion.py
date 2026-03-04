import customtkinter as ctk

from juego.pantalla_juego_config import MODAL_BASE_SIZES
from juego.pantalla_juego_modales_base import ModalBase


class ConfirmationModal(ModalBase):

    def __init__(
        self,
        parent,
        title,
        message,
        on_confirm_callback,
        on_cancel_callback=None,
        confirm_text="Yes",
        cancel_text="No",
        initial_scale=1.0,
    ):
        super().__init__(parent, initial_scale)
        self.title_text = title
        self.message = message
        self.on_confirm_callback = on_confirm_callback
        self.on_cancel_callback = on_cancel_callback
        self.confirm_text = confirm_text
        self.cancel_text = cancel_text

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
        self.create_modal(width, height, self.title_text)
        container = self.create_container(sizes["corner_r"], sizes["border_w"])
        self.create_header(
            container,
            self.title_text,
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
            text=self.message,
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
            text=self.cancel_text,
            font=sizes["button_font"],
            fg_color="#D0D6E0",
            hover_color="#B8C0D0",
            text_color=self.COLORS["text_white"],
            command=self.handle_cancel,
            width=sizes["btn_w"],
            height=sizes["btn_h"],
            corner_radius=sizes["btn_r"],
        ).grid(row=0, column=0, padx=(0, sizes["pad"]))
        ctk.CTkButton(
            btn_frame,
            text=self.confirm_text,
            font=sizes["button_font"],
            fg_color=self.COLORS["primary_blue"],
            hover_color=self.COLORS["primary_hover"],
            text_color=self.COLORS["text_white"],
            command=self.handle_confirm,
            width=sizes["btn_w"],
            height=sizes["btn_h"],
            corner_radius=sizes["btn_r"],
        ).grid(row=0, column=1, padx=(sizes["pad"], 0))
        self.modal.protocol("WM_DELETE_WINDOW", self.handle_cancel)
        self.modal.bind("<Escape>", self.handle_cancel_event)
        self.modal.bind("<Return>", self.handle_confirm_event)

    def handle_cancel_event(self):
        self.handle_cancel()

    def handle_confirm_event(self):
        self.handle_confirm()

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

    def handle_confirm(self):
        self.close()
        if self.on_confirm_callback:
            self.on_confirm_callback()

    def handle_cancel(self):
        self.close()
        if self.on_cancel_callback:
            self.on_cancel_callback()

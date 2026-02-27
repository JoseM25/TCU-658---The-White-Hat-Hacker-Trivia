import customtkinter as ctk


class ModalWidgetFactory:

    def __init__(self, config, fonts, sizes):
        self.config = config
        self.fonts = fonts
        self.sizes = sizes

    def create_label(self, parent, text, font_key="dialog_label", **kwargs):
        defaults = {
            "font": self.fonts[font_key],
            "text_color": self.config.TEXT_DARK,
            "anchor": "w",
        }
        return ctk.CTkLabel(parent, text=text, **{**defaults, **kwargs})

    def create_entry(self, parent, placeholder, **kwargs):
        defaults = {
            "fg_color": self.config.BG_WHITE,
            "text_color": self.config.TEXT_DARK,
            "border_color": self.config.BORDER_MEDIUM,
            "border_width": 2,
            "height": self.sizes.get("entry_height", 36),
            "font": self.fonts["body"],
            "corner_radius": self.sizes.get("corner_radius", 12),
        }
        return ctk.CTkEntry(
            parent, placeholder_text=placeholder, **{**defaults, **kwargs}
        )

    def create_button(self, parent, text, command, is_primary=True, **kwargs):
        if is_primary:
            defaults = {
                "font": self.fonts["button"],
                "fg_color": self.config.PRIMARY_BLUE,
                "hover_color": self.config.PRIMARY_BLUE_HOVER,
            }
        else:
            defaults = {
                "font": self.fonts["cancel_button"],
                "fg_color": self.config.BUTTON_CANCEL_BG,
                "text_color": self.config.TEXT_WHITE,
                "hover_color": self.config.BUTTON_CANCEL_HOVER,
            }

        defaults.update(
            {
                "width": self.sizes.get("button_width", 110),
                "height": self.sizes.get("button_height", 36),
                "corner_radius": self.sizes.get("button_corner_radius", 10),
            }
        )

        return ctk.CTkButton(
            parent, text=text, command=command, **{**defaults, **kwargs}
        )

    def create_frame(self, parent, fg_color="transparent", **kwargs):
        return ctk.CTkFrame(parent, fg_color=fg_color, **kwargs)

    def create_header_frame(self, parent, height=72):
        frame = ctk.CTkFrame(
            parent, fg_color=self.config.BG_MODAL_HEADER, corner_radius=0, height=height
        )
        frame.grid_propagate(False)
        frame.grid_columnconfigure(0, weight=1)
        return frame


class ModalLayoutBuilder:

    def __init__(self, factory):
        self.factory = factory

    def create_container(self, modal, config):
        container = self.factory.create_frame(
            modal, fg_color=config.BG_LIGHT, corner_radius=0
        )
        container.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(1, weight=1)
        return container

    def create_header(self, container, title, fonts, config):
        header_frame = self.factory.create_header_frame(container)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 24), padx=0)

        title_label = ctk.CTkLabel(
            header_frame,
            text=title,
            font=fonts["dialog_title"],
            text_color=config.TEXT_WHITE,
            anchor="center",
            justify="center",
        )
        title_label.grid(row=0, column=0, sticky="nsew", padx=24, pady=(28, 12))

        return header_frame, title_label

    def create_button_row(self, container, button_configs):
        buttons_frame = self.factory.create_frame(container)
        buttons_frame.grid(row=2, column=0, sticky="ew", pady=(0, 28), padx=20)

        for i in range(4):
            buttons_frame.grid_columnconfigure(i, weight=1 if i in (0, 3) else 0)

        buttons = []
        for col, config in enumerate(button_configs, start=1):
            btn = self.factory.create_button(
                buttons_frame,
                text=config["text"],
                command=config["command"],
                is_primary=config.get("is_primary", True),
                **config.get("kwargs", {})
            )

            padx = config.get("padx", (0, 32) if col == 1 else (32, 0))
            btn.grid(row=0, column=col, sticky=config.get("sticky", "e"), padx=padx)
            buttons.append(btn)

        return buttons_frame, buttons


class ScaledWidgetResizer:

    def __init__(self, scaler):
        self.scaler = scaler

    def resize_button(self, button, scale, base_sizes):
        if not button or not button.winfo_exists():
            return

        s = self.scaler.scale_value
        button.configure(
            width=s(base_sizes["button_width"], scale),
            height=s(base_sizes["button_height"], scale),
            corner_radius=s(base_sizes["button_corner_radius"], scale),
        )

    def resize_entry(self, entry, scale, base_sizes):
        if not entry or not entry.winfo_exists():
            return

        s = self.scaler.scale_value
        entry.configure(
            height=s(base_sizes["entry_height"], scale),
            corner_radius=s(base_sizes["corner_radius"], scale),
        )

    def apply_grid_padding(self, widget, scale, base_padding):
        if not widget or not widget.winfo_exists():
            return

        s = self.scaler.scale_value

        try:
            padx = base_padding.get("padx", 0)
            pady = base_padding.get("pady", 0)
        except AttributeError:
            return

        try:
            padx = tuple(s(p, scale) for p in padx)
        except TypeError:
            padx = s(padx, scale)

        try:
            pady = tuple(s(p, scale) for p in pady)
        except TypeError:
            pady = s(pady, scale)

        widget.grid_configure(padx=padx, pady=pady)

import tkinter as tk

from juego.ayudantes_responsivos import get_logical_dimensions


class QuestionScreenLayoutMixin:

    def measure_widget_width(self, widget, fallback):
        if widget and widget.winfo_exists():
            try:
                widget.update_idletasks()
            except tk.TclError:
                pass
            width = widget.winfo_width()
            if width > 1:
                return width
        return fallback

    def get_effective_detail_width(self):
        fallback = self.size_state.get(
            "detail_width_estimate", self.BASE_DIMENSIONS[0] // 2
        )
        return self.measure_widget_width(
            getattr(self, "detail_body_frame", None), fallback
        )

    def get_detail_viewport_width(self):
        content = getattr(self, "detail_content_frame", None)
        fallback = self.size_state.get(
            "detail_width_estimate", self.BASE_DIMENSIONS[0] // 2
        )
        if not content or not content.winfo_exists():
            return fallback

        canvas = getattr(content, "_parent_canvas", None)
        if canvas and canvas.winfo_exists():
            try:
                canvas.update_idletasks()
            except tk.TclError:
                pass
            width = canvas.winfo_width()
            if width > 1:
                return width

        return self.measure_widget_width(content, fallback)

    def get_visible_detail_width(self):
        window_width = max(
            getattr(self, "current_window_width", self.BASE_DIMENSIONS[0]), 200
        )
        sidebar_fallback = self.size_state.get(
            "sidebar_width_estimate", window_width // 3
        )
        sidebar_width = self.measure_widget_width(
            getattr(self, "sidebar_frame", None), sidebar_fallback
        )
        divider_width = self.measure_widget_width(
            getattr(self, "divider_frame", None), 2
        )
        outer_margin = self.scale_value(72, self.current_scale or 1, 40, 140)
        visible_width = window_width - sidebar_width - divider_width - outer_margin
        return max(120, visible_width)

    def interpolate_profile(self, value, profile):
        return self.scaler.interpolate_profile(value, profile)

    def clamp_value(self, value, min_value=None, max_value=None):
        return self.scaler.clamp_value(value, min_value, max_value)

    def get_wrap_ratio(self, width=None):
        target_width = (
            width if width is not None else self.size_state.get("detail_width_estimate")
        )
        if not target_width:
            target_width = self.BASE_DIMENSIONS[0] * 0.6
        return self.layout_calc.calculate_wrap_ratio(target_width)

    def compute_definition_padding(self, width=None):
        target_width = width if width is not None else self.get_effective_detail_width()
        return self.layout_calc.compute_definition_padding(
            target_width, self.current_scale
        )

    def get_sidebar_share(self, window_width):
        return self.size_calc.get_sidebar_share(window_width)

    def scale_value(self, base, scale, min_value=None, max_value=None):
        return self.scaler.scale_value(base, scale, min_value, max_value)

    def apply_title_wraplength(self):
        if not self.detail_title_label or not self.detail_title_label.winfo_exists():
            return
        fallback = self.size_state.get("detail_width_estimate", 600)
        width = self.measure_widget_width(self.detail_header_frame, fallback)
        width -= max(40, self.header_pad or 0)
        wrap_target = max(120, width)
        self.detail_title_label.configure(wraplength=wrap_target)

    def header_value(self, value):
        return value * self.HEADER_SIZE_MULTIPLIER

    def update_size_state(self, scale, window_width):
        self.size_state = self.size_calc.calculate_sizes(scale, window_width)

        if self.main_frame and self.main_frame.winfo_exists():
            self.main_frame.grid_columnconfigure(
                0, minsize=self.size_state["sidebar_minsize"]
            )
            self.main_frame.grid_columnconfigure(
                2, minsize=self.size_state["detail_minsize"]
            )

    def update_fonts(self, scale):
        for name, base_size in self.font_base_sizes.items():
            font = getattr(self, f"{name}_font", None)
            if not font:
                continue
            min_size = self.font_min_sizes.get(name, 10)
            max_size = base_size * 2.2
            font.configure(size=self.scale_value(base_size, scale, min_size, max_size))

    def refresh_icons(self, scale):
        limits = {
            "audio": (18, 64),
            "search": (12, 32),
            "back": (16, 40),
        }
        for key, base_size in self.icon_base_sizes.items():
            min_limit, max_limit = limits.get(key, (12, 48))
            size = (
                self.scale_value(base_size[0], scale, min_limit, max_limit),
                self.scale_value(base_size[1], scale, min_limit, max_limit),
            )
            cached = self.icon_cache.get(key)
            if cached and cached["size"] == size:
                image = cached["image"]
            else:
                image = self.image_handler.create_ctk_icon(self.ICONS[key], size)
                self.icon_cache[key] = {"size": size, "image": image}

            if key == "audio":
                self.audio_icon = image
                if (
                    self.definition_audio_button
                    and self.definition_audio_button.winfo_exists()
                ):
                    if image:
                        self.definition_audio_button.configure(image=image, text="")
                    else:
                        self.definition_audio_button.configure(image=None, text="Audio")
            elif key == "search":
                self.search_icon = image
                if self.search_icon_label and self.search_icon_label.winfo_exists():
                    if image:
                        self.search_icon_label.configure(
                            image=image, text="", width=size[0]
                        )
                    else:
                        self.search_icon_label.configure(
                            image=None,
                            text="S",
                            font=self.button_font,
                            text_color=self.COLORS["text_white"],
                        )
            elif key == "back":
                self.back_arrow_icon = image
                if self.menu_button and self.menu_button.winfo_exists():
                    self.menu_button.configure(image=image)

    def update_header_layout(self, scale):
        if not self.menu_button or not self.menu_button.winfo_exists():
            return

        header_val = self.header_value
        pad_top = self.scale_value(
            header_val(24), scale, header_val(12), header_val(64)
        )
        pad_bottom = self.scale_value(
            header_val(30), scale, header_val(14), header_val(72)
        )
        pad_left = self.scale_value(
            header_val(28), scale, header_val(10), header_val(84)
        )
        pad_right = self.scale_value(
            header_val(20), scale, header_val(8), header_val(56)
        )

        self.menu_button.grid_configure(
            padx=(pad_left, pad_right), pady=(pad_top, pad_bottom)
        )
        self.menu_button.configure(
            width=self.scale_value(
                header_val(130), scale, header_val(80), header_val(280)
            ),
            height=self.scale_value(
                header_val(48), scale, header_val(32), header_val(96)
            ),
            corner_radius=self.scale_value(
                header_val(12), scale, header_val(6), header_val(28)
            ),
        )

        if self.header_title_label and self.header_title_label.winfo_exists():
            self.header_title_label.grid_configure(
                padx=self.scale_value(
                    header_val(40), scale, header_val(14), header_val(96)
                ),
                pady=(pad_top, pad_bottom),
            )

        if self.divider_frame and self.divider_frame.winfo_exists():
            self.divider_frame.grid_configure(pady=self.scale_value(32, scale, 12, 72))
            self.divider_frame.configure(width=self.scale_value(2, scale, 1, 4))

    def update_sidebar_layout(self, scale):
        if not self.sidebar_frame or not self.sidebar_frame.winfo_exists():
            return

        pad_left = self.scale_value(28, scale, 10, 60)
        pad_right = self.scale_value(10, scale, 6, 40)
        pad_vertical = self.scale_value(32, scale, 12, 76)

        self.sidebar_frame.grid_configure(padx=(pad_left, pad_right), pady=pad_vertical)

        search_padx_left = self.scale_value(14, scale, 6, 32)
        search_padx_right = self.scale_value(10, scale, 6, 28)
        search_pady = self.scale_value(16, scale, 6, 36)
        if self.search_wrapper and self.search_wrapper.winfo_exists():
            self.search_wrapper.grid_configure(
                padx=(search_padx_left, search_padx_right), pady=search_pady
            )
            self.search_wrapper.configure(
                corner_radius=self.scale_value(18, scale, 10, 32)
            )

        if self.search_entry and self.search_entry.winfo_exists():
            self.search_entry.grid_configure(
                padx=(
                    self.scale_value(4, scale, 2, 18),
                    self.scale_value(18, scale, 8, 32),
                ),
                pady=self.scale_value(4, scale, 2, 18),
            )
            self.search_entry.configure(height=self.scale_value(42, scale, 28, 66))

        if self.search_icon_label and self.search_icon_label.winfo_exists():
            self.search_icon_label.grid_configure(
                padx=(
                    self.scale_value(12, scale, 6, 24),
                    self.scale_value(4, scale, 2, 16),
                )
            )

        if self.add_button and self.add_button.winfo_exists():
            self.add_button.grid_configure(
                padx=(
                    self.scale_value(0, scale, 0, 8),
                    self.scale_value(16, scale, 8, 36),
                ),
                pady=search_pady,
            )
            self.add_button.configure(
                width=self.scale_value(96, scale, 72, 200),
                height=self.scale_value(42, scale, 30, 72),
                corner_radius=self.scale_value(12, scale, 8, 24),
            )

        self.update_list_container_layout(scale)

    def update_list_container_layout(self, scale):
        if not self.list_container or not self.list_container.winfo_exists():
            return
        pad_y = self.scale_value(20, scale, 8, 40)
        self.list_container.grid_configure(padx=(0, 0), pady=(pad_y, 0))

    def update_detail_layout(self, scale):
        if not self.detail_container or not self.detail_container.winfo_exists():
            return

        detail_width = self.get_effective_detail_width()
        base_pad_left = 12
        base_pad_right = 32
        pad_left = self.scale_value(base_pad_left, scale, 6, 40)
        pad_right = self.scale_value(base_pad_right, scale, 12, 70)
        pad_vertical = self.scale_value(32, scale, 12, 76)

        self.detail_container.grid_configure(
            padx=(pad_left, pad_right), pady=pad_vertical
        )
        self.detail_container.configure(
            corner_radius=self.scale_value(16, scale, 10, 32)
        )
        panel_height = self.size_state.get("detail_panel_height", 520)
        scroll_height = self.size_state.get(
            "detail_scroll_height", max(180, panel_height - 140)
        )
        self.detail_container.grid_rowconfigure(1, minsize=panel_height)

        body_padx = self.scale_value(24, scale, 12, 56)
        if detail_width <= 640:
            body_padx = max(8, int(round(body_padx * 0.5)))
        body_pady = self.scale_value(24, scale, 12, 64)
        if self.detail_body_frame and self.detail_body_frame.winfo_exists():
            self.detail_body_frame.grid_configure(padx=body_padx, pady=(0, body_pady))
            self.detail_body_frame.configure(height=panel_height)
            self.body_pad = body_padx * 2

        image_pad_top = self.scale_value(28, scale, 12, 56)
        image_pad_bottom = self.scale_value(48, scale, 16, 96)
        image_padx = self.scale_value(12, scale, 6, 32)

        if self.detail_content_frame and self.detail_content_frame.winfo_exists():
            self.detail_content_frame.configure(height=scroll_height)

        header_padx = self.scale_value(24, scale, 12, 56)
        if self.detail_header_frame and self.detail_header_frame.winfo_exists():
            self.detail_header_frame.grid_configure(padx=header_padx)
            self.header_pad = header_padx * 2

        if self.detail_image_label and self.detail_image_label.winfo_exists():
            width, height = self.size_state.get(
                "detail_image", self.SIZES["detail_image"]
            )
            self.detail_image_label.grid_configure(
                pady=(image_pad_top, image_pad_bottom), padx=image_padx
            )
            self.detail_image_label.configure(width=width, height=height)

        if self.definition_row and self.definition_row.winfo_exists():
            definition_pad = self.compute_definition_padding(detail_width)
            if detail_width <= 640:
                definition_pad = max(4, int(round(definition_pad * 0.55)))
            self.definition_row.grid_configure(
                padx=definition_pad,
                pady=(self.scale_value(32, scale, 12, 60), 0),
            )
            self.definition_pad = definition_pad * 2

        if self.definition_audio_button and self.definition_audio_button.winfo_exists():
            button_width = self.scale_value(44, scale, 30, 76)
            button_gap = self.scale_value(16, scale, 10, 26)
            self.definition_audio_button.configure(
                width=button_width,
                height=self.scale_value(44, scale, 30, 76),
                corner_radius=self.scale_value(22, scale, 14, 40),
            )
            self.definition_audio_button.grid_configure(padx=(0, button_gap))
            self.definition_button_gap = button_gap
            self.definition_button_width = button_width + button_gap

        self.update_definition_audio_layout(detail_width, scale)

        for button in self.detail_action_buttons:
            if button and button.winfo_exists():
                button.configure(
                    width=self.scale_value(110, scale, 80, 240),
                    height=self.scale_value(44, scale, 30, 80),
                    corner_radius=self.scale_value(12, scale, 8, 24),
                )

        self.refresh_detail_image()
        if self.parent and self.parent.winfo_exists():
            try:
                self.parent.after_idle(self.apply_title_wraplength)
            except tk.TclError:
                self.apply_title_wraplength()

        if self.detail_title_label and self.detail_title_label.winfo_exists():
            base_size = self.font_base_sizes.get("detail_title", 38)
            min_size = self.font_min_sizes.get("detail_title", 12)
            max_size = base_size * 2.2
            current_font_size = self.scale_value(base_size, scale, min_size, max_size)
            title_height = int(current_font_size * 1.35 * 2)
            self.detail_title_label.configure(height=title_height)

        if hasattr(self, "queue_detail_scroll_update"):
            self.queue_detail_scroll_update()

    def update_definition_audio_layout(self, container_width, scale):
        if not self.definition_row or not self.definition_row.winfo_exists():
            return
        if not self.definition_audio_button or not self.detail_definition_textbox:
            return

        should_stack = self.layout_calc.should_stack_layout(
            container_width, scale, self.DEFINITION_STACK_BREAKPOINT
        )
        target_inline = not should_stack

        if target_inline == self.definition_layout_inline:
            return

        self.definition_layout_inline = target_inline
        stack_gap = self.scale_value(10, scale, 6, 22)

        if should_stack:
            self.definition_row.grid_columnconfigure(0, weight=1)
            self.definition_row.grid_columnconfigure(1, weight=0)
            self.definition_audio_button.grid_configure(
                row=0,
                column=0,
                columnspan=2,
                sticky="w",
                pady=(0, stack_gap),
                padx=(0, 0),
            )
            self.detail_definition_textbox.grid_configure(
                row=1, column=0, columnspan=2, sticky="nsew"
            )
        else:
            self.definition_row.grid_columnconfigure(0, weight=0)
            self.definition_row.grid_columnconfigure(1, weight=1)
            self.definition_audio_button.grid_configure(
                row=0,
                column=0,
                columnspan=1,
                sticky="nw",
                pady=0,
                padx=(0, self.definition_button_gap),
            )
            self.detail_definition_textbox.grid_configure(
                row=0, column=1, columnspan=1, sticky="nsew"
            )

    def apply_responsive(self):
        if not self.parent or not self.parent.winfo_exists():
            return

        width, height = get_logical_dimensions(self.parent, self.BASE_DIMENSIONS)
        self.current_window_width = width
        self.current_window_height = height

        scale = self.scaler.calculate_scale(
            width, height, low_res_profile=self.LOW_RES_SCALE_PROFILE
        )
        self.current_scale = scale

        self.update_size_state(scale, width)
        self.update_fonts(scale)
        self.refresh_icons(scale)
        self.update_header_layout(scale)
        self.update_sidebar_layout(scale)
        self.update_detail_layout(scale)

        metrics_snapshot = (
            self.size_state.get("question_btn_height"),
            self.size_state.get("question_margin"),
            self.size_state.get("question_padding"),
            self.size_state.get("question_corner_radius"),
            self.size_state.get("max_questions"),
            self.list_frame_padding,
            self.list_frame_corner_radius,
            self.size_state.get("detail_panel_height"),
            self.size_state.get("detail_scroll_height"),
        )
        needs_render = metrics_snapshot != self.render_metric_snapshot
        self.render_metric_snapshot = metrics_snapshot

        if needs_render:
            self.render_question_list()

        self.resize_current_modal()
        self.resize_job = None

    def resize_current_modal(self):
        if not self.current_modal:
            return

        root = None
        try:
            root = self.parent.winfo_toplevel()
        except tk.TclError:
            root = self.parent

        scale = None
        if hasattr(self.current_modal, "get_responsive_scale"):
            try:
                scale = self.current_modal.get_responsive_scale(root)
            except tk.TclError:
                scale = None

        if scale is None:
            return

        try:
            self.current_modal.resize(scale)
        except (AttributeError, tk.TclError):
            pass

    def on_resize(self, event):
        if event.widget is not self.parent:
            return
        if self.resize_job:
            try:
                self.parent.after_cancel(self.resize_job)
            except tk.TclError:
                pass
        self.resize_job = self.parent.after(self.RESIZE_DELAY, self.apply_responsive)

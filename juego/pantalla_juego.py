import tkinter as tk

from juego.juego_logica import GameScreenLogic


class GameScreen(GameScreenLogic):

    def __init__(self, parent, on_return_callback=None, tts_service=None):
        super().__init__(parent, on_return_callback, tts_service)

        self.parent.bind("<Configure>", self.on_resize)
        self.bind_physical_keyboard()
        self.apply_responsive()

        self.load_random_question()
        self.start_timer()

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
        self.image_frame.configure(height=image_size)
        self.image_label.configure(width=image_size, height=image_size)

        if self.current_image and self.current_question:
            self.load_question_image()

        wrap_length = int(max(300, min(800, 600 * scale)))
        self.definition_label.configure(wraplength=wrap_length)

        box_size = self.get_scaled_box_size(scale)
        visible_boxes = [b for b in self.answer_box_labels if b.winfo_manager()]
        for box in self.answer_box_labels:
            box.configure(width=box_size, height=box_size)
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

    def bind_physical_keyboard(self):
        root = self.parent.winfo_toplevel()
        root.bind("<KeyPress>", self.on_physical_key_press)
        root.bind("<KeyRelease>", self.on_physical_key_release)

    def unbind_physical_keyboard(self):
        try:
            root = self.parent.winfo_toplevel()
            root.unbind("<KeyPress>")
            root.unbind("<KeyRelease>")
        except tk.TclError:
            pass

    def on_physical_key_press(self, event):
        if self.is_modal_open():
            return

        key_char = event.char.upper() if event.char else ""
        key_sym = event.keysym

        if key_sym == "Return":
            self.simulate_button_press(self.check_button)
            self.on_check()
            return

        if self.awaiting_modal_decision:
            return

        if key_char.isalpha() and len(key_char) == 1:
            self.show_key_feedback(key_char)
            self.on_key_press(key_char)
            return

        if key_sym == "BackSpace":
            self.show_key_feedback("⌫")
            self.on_key_press("⌫")
            return

        if key_sym == "Escape":
            self.simulate_button_press(self.skip_button)
            self.on_skip()
            return

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

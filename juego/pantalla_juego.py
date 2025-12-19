import tkinter as tk

import customtkinter as ctk

from juego.pantalla_juego_config import GAME_PROFILES, GAME_RESIZE_DELAY
from juego.pantalla_juego_logica import GameScreenLogic


class GameScreen(GameScreenLogic):

    def __init__(self, parent, on_return_callback=None, tts_service=None):
        super().__init__(parent, on_return_callback, tts_service)

        # Bind resize event
        self.parent.bind("<Configure>", self.on_resize)

        # Bind physical keyboard
        self.bind_physical_keyboard()

        # Initial responsive layout
        self.apply_responsive()

        # Start the game
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

        # Get current dimensions
        width = max(self.parent.winfo_width(), 1)
        height = max(self.parent.winfo_height(), 1)

        # Calculate scale using profile
        low_res_profile = GAME_PROFILES.get("low_res")
        scale = self.scaler.calculate_scale(width, height, low_res_profile)

        # Update size state
        self.size_state = self.size_calc.calculate_sizes(scale, width, height)
        needed_height = self._estimate_layout_height(self.size_state)
        if needed_height > height:
            fit_ratio = height / needed_height
            fit_scale = max(
                self.scaler.min_scale, min(self.scaler.max_scale, scale * fit_ratio)
            )
            self.size_state = self.size_calc.calculate_sizes(fit_scale, width, height)
            scale = fit_scale
            needed_height = self._estimate_layout_height(self.size_state)
        self._apply_keyboard_squeeze(needed_height, height)
        self.current_scale = scale
        self.current_window_width = width
        self.current_window_height = height

        # Update all components
        self._update_fonts(scale)
        self._update_header(scale)
        self._update_question_container()
        self._update_keyboard()
        self._update_action_buttons(scale)
        self._update_wildcards(scale)

        # Resize any open modals
        self._resize_modals(scale)

        # Clear resize job
        self.resize_job = None

    def _estimate_layout_height(self, sizes):
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
            def_pad_y = self.scale_value(6, scale, 3, 12)
            def_height = self.scale_value(42, scale, 38, 50)
        else:
            def_pad_y = self.scale_value(14, scale, 8, 36)
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
        feedback_row = feedback_pad + self.scale_value(12, scale, 8, 16)

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

        keyboard_height = 3 * (
            sizes["key_size"] + sizes["key_row_gap"] * 2
        ) + sizes["keyboard_pad_y"]
        action_height = sizes["action_button_height"] + self.scale_value(
            24, scale, 12, 48
        )

        return header_h + container_pad + question_height + keyboard_height + action_height

    def _estimate_keyboard_height(self, sizes):
        return 3 * (
            sizes["key_size"] + sizes["key_row_gap"] * 2
        ) + sizes["keyboard_pad_y"]

    def _apply_keyboard_squeeze(self, needed_height, height):
        if not self.size_state:
            return

        sizes = self.size_state
        kb_height = self._estimate_keyboard_height(sizes)
        if kb_height <= 0:
            return

        is_compact = sizes.get("is_height_constrained", False)
        overflow = max(0, needed_height - height)

        # Always shrink keyboard a bit on height-constrained screens (720p class)
        base_squeeze = 1.0
        if is_compact:
            base_squeeze = 0.88 if height <= 720 else 0.92

        squeeze = base_squeeze
        if overflow > 0:
            min_ratio = 0.72 if is_compact else 0.8
            target_height = max(kb_height - overflow, kb_height * min_ratio)
            overflow_squeeze = max(min_ratio, min(1.0, target_height / kb_height))
            squeeze = min(squeeze, overflow_squeeze)

        if squeeze >= 0.999:
            return

        sizes["key_size"] = max(16, int(round(sizes["key_size"] * squeeze)))
        sizes["key_gap"] = max(2, int(round(sizes["key_gap"] * squeeze)))
        sizes["key_row_gap"] = max(1, int(round(sizes["key_row_gap"] * squeeze)))
        sizes["keyboard_pad_y"] = max(4, int(round(sizes["keyboard_pad_y"] * squeeze)))
        sizes["delete_icon"] = max(12, int(round(sizes["delete_icon"] * squeeze)))

    def _update_fonts(self, scale):
        self.font_registry.update_scale(scale, self.scaler)

    def _update_header(self, scale):
        sizes = self.size_state

        # Header frame height
        if self.header_frame and self.header_frame.winfo_exists():
            self.header_frame.configure(height=sizes["header_height"])

        # Header container padding
        pad_x = sizes["header_pad_x"]
        pad_y = sizes["header_pad_y"]

        if self.header_left_container and self.header_left_container.winfo_exists():
            self.header_left_container.grid_configure(padx=(pad_x, 0), pady=pad_y)

        if self.header_right_container and self.header_right_container.winfo_exists():
            self.header_right_container.grid_configure(padx=(0, pad_x), pady=pad_y)

        if self.header_center_container and self.header_center_container.winfo_exists():
            self.header_center_container.grid_configure(pady=pad_y)

        # Update header icons
        self._update_header_icons()

        # Update audio button
        self._update_audio_button(scale)

    def _update_header_icons(self):
        sizes = self.size_state

        # Clock icon
        if self.clock_icon:
            sz = sizes["timer_icon"]
            self.clock_icon.configure(size=(sz, sz))

        # Star icon
        if self.star_icon:
            sz = sizes["star_icon"]
            self.star_icon.configure(size=(sz, sz))

        # Freeze icon (for timer)
        if self.freeze_icon:
            sz = sizes["timer_icon"]
            self.freeze_icon.configure(size=(sz, sz))

    def _update_audio_button(self, scale):
        sizes = self.size_state
        icon_sz = sizes["audio_icon"]
        btn_width = sizes["audio_button_width"]
        btn_height = sizes["audio_button_height"]
        corner_r = self.scale_value(8, scale, 6, 16)

        # Update icon sizes
        for icon in (self.audio_icon_on, self.audio_icon_off):
            if icon:
                icon.configure(size=(icon_sz, icon_sz))

        # Update button size
        if self.audio_toggle_btn and self.audio_toggle_btn.winfo_exists():
            self.audio_toggle_btn.configure(
                width=btn_width,
                height=btn_height,
                corner_radius=corner_r,
            )

    def _update_question_container(self):
        sizes = self.size_state

        if not self.question_container or not self.question_container.winfo_exists():
            return

        # Container padding and corner radius
        pad_x = sizes["container_pad_x"]
        pad_y = sizes["container_pad_y"]
        corner_r = sizes["container_corner_radius"]

        self.question_container.grid_configure(padx=pad_x, pady=pad_y)
        self.question_container.configure(corner_radius=corner_r)

        # Update sub-components
        self._update_image()
        self._update_definition()
        self._update_answer_boxes()
        self._update_feedback()

    def _update_image(self):
        sizes = self.size_state
        scale = sizes.get("scale", 1.0)
        is_compact = sizes.get("is_height_constrained", False)
        img_sz = sizes["image_size"]

        if self.image_frame and self.image_frame.winfo_exists():
            self.image_frame.configure(height=img_sz)
            # Scale image padding - reduce at low res, expand at high res
            if is_compact:
                pad_top = self.scale_value(12, scale, 6, 20)
                pad_bottom = self.scale_value(6, scale, 3, 10)
            else:
                pad_top = self.scale_value(24, scale, 12, 60)
                pad_bottom = self.scale_value(12, scale, 6, 30)
            self.image_frame.grid_configure(pady=(pad_top, pad_bottom))

        if self.image_label and self.image_label.winfo_exists():
            self.image_label.configure(width=img_sz, height=img_sz)

        # Reload image at new size
        if self.current_image and self.current_question:
            self.load_question_image()

    def _update_definition(self):
        sizes = self.size_state
        scale = sizes.get("scale", 1.0)
        is_compact = sizes.get("is_height_constrained", False)

        # Update definition frame padding responsively
        if self.definition_frame and self.definition_frame.winfo_exists():
            if is_compact:
                # Tighter padding for height-constrained screens
                pad_x = self.scale_value(20, scale, 10, 40)
                pad_y = self.scale_value(6, scale, 3, 12)
            else:
                # Normal padding for larger screens - expand more at high res
                pad_x = self.scale_value(36, scale, 20, 80)
                pad_y = self.scale_value(14, scale, 8, 36)
            self.definition_frame.grid_configure(padx=pad_x, pady=pad_y)

        # Update scrollable frame wrapper height for long definitions
        if (
            self.definition_scroll_wrapper
            and self.definition_scroll_wrapper.winfo_exists()
        ):
            if is_compact:
                max_height = self.scale_value(42, scale, 38, 50)
            else:
                max_height = self.scale_value(50, scale, 42, 65)
            self.definition_scroll_wrapper.configure(height=max_height)

        if self.definition_label and self.definition_label.winfo_exists():
            wrap = sizes["definition_wrap"]
            self.definition_label.configure(wraplength=wrap)

        # Update info icon
        if self.info_icon:
            sz = sizes["info_icon"]
            self.info_icon.configure(size=(sz, sz))

    def _update_answer_boxes(self):
        sizes = self.size_state
        scale = sizes.get("scale", 1.0)
        is_compact = sizes.get("is_height_constrained", False)
        box_sz = sizes["answer_box"]
        gap = sizes["answer_box_gap"]
        extra_pad = self.scale_value(16, scale, 8, 20)

        # Update answer box labels - only update boxes that are currently visible (managed)
        # Using grid_configure on a grid_remove()'d widget would re-show it!
        visible_boxes = [b for b in self.answer_box_labels if b.winfo_manager()]
        for box in visible_boxes:
            if box and box.winfo_exists():
                box.configure(width=box_sz, height=box_sz)
                box.grid_configure(padx=gap, pady=4)

        # Update frame size if we have visible boxes (extra height padding to prevent clipping)
        if (
            visible_boxes
            and self.answer_boxes_frame
            and self.answer_boxes_frame.winfo_exists()
        ):
            frame_width = len(visible_boxes) * (box_sz + gap * 2)
            frame_height = box_sz + extra_pad
            self.answer_boxes_frame.configure(width=frame_width, height=frame_height)
            # Update answer boxes frame padding - reduce at low res, expand at high res
            if is_compact:
                pad_y = self.scale_value(8, scale, 6, 12)
            else:
                pad_y = self.scale_value(14, scale, 8, 28)
            self.answer_boxes_frame.grid_configure(pady=(pad_y, pad_y // 2))

    def _update_feedback(self):
        sizes = self.size_state
        is_compact = sizes.get("is_height_constrained", False)

        if self.feedback_label and self.feedback_label.winfo_exists():
            pad_bottom = sizes["feedback_pad_bottom"]
            # Reduce feedback padding at low res
            if is_compact:
                pad_bottom = max(6, pad_bottom // 2)
            self.feedback_label.grid_configure(pady=(0, pad_bottom))

    def _update_keyboard(self):
        sizes = self.size_state
        key_sz = sizes["key_size"]
        key_gap = sizes["key_gap"]
        key_row_gap = sizes["key_row_gap"]
        keyboard_pad = sizes["keyboard_pad"]
        keyboard_pad_y = sizes["keyboard_pad_y"]

        # Force an obvious keyboard shrink on small screens.
        height = self.current_window_height
        keyboard_scale = 0.85 if height <= 1200 else 1.0

        if keyboard_scale < 1.0:
            key_sz = max(6, int(round(key_sz * keyboard_scale)))
            key_gap = max(0, int(round(key_gap * keyboard_scale)))
            key_row_gap = max(0, int(round(key_row_gap * keyboard_scale)))
            keyboard_pad = max(0, int(round(keyboard_pad * keyboard_scale)))
            keyboard_pad_y = max(0, int(round(keyboard_pad_y * keyboard_scale)))
            delete_scale = keyboard_scale
            sizes["delete_icon"] = max(
                6, int(round(sizes["delete_icon"] * delete_scale))
            )

            scale = sizes.get("scale", 1.0)
            base_size = self.font_base_sizes.get("keyboard", 18)
            min_size = self.font_min_sizes.get("keyboard", 10)
            new_size = max(6, int(round(base_size * scale * keyboard_scale)))
            self.keyboard_font.configure(size=new_size)
        delete_width = int(key_sz * sizes["delete_key_width_ratio"])

        if self.keyboard_frame and self.keyboard_frame.winfo_exists():
            self.keyboard_frame.grid_configure(
                padx=keyboard_pad, pady=(0, keyboard_pad_y)
            )

        # Update keyboard row gaps
        for row_frame in self.keyboard_frame.winfo_children():
            if row_frame and row_frame.winfo_exists():
                row_frame.grid_configure(pady=key_row_gap)

        # Update all keyboard buttons
        for btn in self.keyboard_buttons:
            if btn and btn.winfo_exists():
                is_delete = btn is self.delete_button
                width = delete_width if is_delete else key_sz
                btn.configure(width=width, height=key_sz)
                btn.grid_configure(padx=key_gap // 2)

        # Update delete icon size
        if self.delete_icon:
            del_sz = sizes["delete_icon"]
            self.delete_icon.configure(size=(del_sz, del_sz))

    def _update_action_buttons(self, scale):
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

        # Update padding for action buttons frame
        if self.action_buttons_frame and self.action_buttons_frame.winfo_exists():
            pad_bottom = self.scale_value(24, scale, 12, 48)
            self.action_buttons_frame.grid_configure(pady=(0, pad_bottom))

    def _update_wildcards(self, scale):
        sizes = self.size_state
        is_compact = sizes.get("is_height_constrained", False)
        wc_sz = sizes["wildcard_size"]
        wc_corner = sizes["wildcard_corner_radius"]
        lightning_sz = sizes["lightning_icon"]
        freeze_sz = sizes["freeze_icon"]
        wc_font_size = sizes["wildcard_font"]
        charges_font_size = sizes["charges_font"]

        # Calculate button width to match build_wildcards_panel (1.5x height for pill shape)
        wc_btn_width = int(wc_sz * 1.5)

        # Scale button gap - reduce at low res, expand at high res
        if is_compact:
            btn_gap = self.scale_value(6, scale, 3, 10)
        else:
            btn_gap = self.scale_value(10, scale, 6, 20)

        # Update wildcard buttons with consistent pill shape
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

        # Update lightning icon
        if self.lightning_icon:
            self.lightning_icon.configure(size=(lightning_sz, lightning_sz))

        # Update freeze wildcard icon
        if self.freeze_wildcard_icon:
            self.freeze_wildcard_icon.configure(size=(freeze_sz, freeze_sz))

        # Update wildcards frame padding - tighter at low res, expand at high res
        if self.wildcards_frame and self.wildcards_frame.winfo_exists():
            if is_compact:
                pad_x = self.scale_value(14, scale, 8, 20)
                pad_y = self.scale_value(10, scale, 6, 18)
            else:
                pad_x = self.scale_value(28, scale, 16, 56)
                pad_y = self.scale_value(28, scale, 16, 56)
            self.wildcards_frame.grid_configure(padx=(0, pad_x), pady=pad_y)

        # Update charges frame padding
        if self.charges_frame and self.charges_frame.winfo_exists():
            charges_pad = (
                self.scale_value(10, scale, 4, 14)
                if is_compact
                else self.scale_value(14, scale, 8, 24)
            )
            self.charges_frame.grid_configure(pady=(0, charges_pad))

        # Update wildcard button fonts
        try:
            wc_font = ctk.CTkFont(
                family="Poppins ExtraBold", size=wc_font_size, weight="bold"
            )
            for btn in [self.wildcard_x2_btn, self.wildcard_hint_btn]:
                if btn and btn.winfo_exists():
                    btn.configure(font=wc_font)
        except tk.TclError:
            pass

        # Update charges label font
        if self.charges_label and self.charges_label.winfo_exists():
            try:
                charges_font = ctk.CTkFont(
                    family="Poppins SemiBold", size=charges_font_size, weight="bold"
                )
                self.charges_label.configure(font=charges_font)
            except tk.TclError:
                pass

        # Update multiplier label font
        if self.multiplier_label and self.multiplier_label.winfo_exists():
            mul_font_size = self.scale_value(20, scale, 12, 36)
            try:
                mul_font = ctk.CTkFont(
                    family="Poppins ExtraBold", size=mul_font_size, weight="bold"
                )
                self.multiplier_label.configure(font=mul_font)
            except tk.TclError:
                pass

    def _resize_modals(self, scale):
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
        for modal_attr in ["completion_modal", "summary_modal", "skip_modal"]:
            modal = getattr(self, modal_attr, None)
            if modal and hasattr(modal, "modal") and modal.modal:
                try:
                    if modal.modal.winfo_exists():
                        return True
                except tk.TclError:
                    pass
        return False

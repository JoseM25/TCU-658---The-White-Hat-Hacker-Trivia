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
        self.current_scale = scale
        self.current_window_width = width
        self.current_window_height = height

        # Update all components
        self._update_fonts(scale)
        self._update_header(scale)
        self._update_question_container(scale)
        self._update_keyboard(scale)
        self._update_action_buttons(scale)
        self._update_wildcards(scale)

        # Resize any open modals
        self._resize_modals(scale)

        # Clear resize job
        self.resize_job = None

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
        self._update_header_icons(scale)

        # Update audio button
        self._update_audio_button(scale)

    def _update_header_icons(self, scale):
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

    def _update_question_container(self, scale):
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
        self._update_image(scale)
        self._update_definition(scale)
        self._update_answer_boxes(scale)
        self._update_feedback(scale)

    def _update_image(self, scale):
        sizes = self.size_state
        img_sz = sizes["image_size"]

        if self.image_frame and self.image_frame.winfo_exists():
            self.image_frame.configure(height=img_sz)

        if self.image_label and self.image_label.winfo_exists():
            self.image_label.configure(width=img_sz, height=img_sz)

        # Reload image at new size
        if self.current_image and self.current_question:
            self.load_question_image()

    def _update_definition(self, scale):
        sizes = self.size_state

        if self.definition_label and self.definition_label.winfo_exists():
            wrap = sizes["definition_wrap"]
            self.definition_label.configure(wraplength=wrap)

        # Update info icon
        if self.info_icon:
            sz = sizes["info_icon"]
            self.info_icon.configure(size=(sz, sz))

    def _update_answer_boxes(self, scale):
        sizes = self.size_state
        box_sz = sizes["answer_box"]
        gap = sizes["answer_box_gap"]

        # Update answer box labels
        for box in self.answer_box_labels:
            if box and box.winfo_exists():
                box.configure(width=box_sz, height=box_sz)
                box.grid_configure(padx=gap)

        # Update frame size if we have visible boxes
        visible_boxes = [b for b in self.answer_box_labels if b.winfo_manager()]
        if (
            visible_boxes
            and self.answer_boxes_frame
            and self.answer_boxes_frame.winfo_exists()
        ):
            frame_width = len(visible_boxes) * (box_sz + gap * 2)
            frame_height = box_sz + 4
            self.answer_boxes_frame.configure(width=frame_width, height=frame_height)

    def _update_feedback(self, scale):
        sizes = self.size_state

        if self.feedback_label and self.feedback_label.winfo_exists():
            pad_bottom = sizes["feedback_pad_bottom"]
            self.feedback_label.grid_configure(pady=(0, pad_bottom))

    def _update_keyboard(self, scale):
        sizes = self.size_state
        key_sz = sizes["key_size"]
        key_gap = sizes["key_gap"]
        keyboard_pad = sizes["keyboard_pad"]
        delete_width = int(key_sz * sizes["delete_key_width_ratio"])

        if self.keyboard_frame and self.keyboard_frame.winfo_exists():
            self.keyboard_frame.grid_configure(padx=keyboard_pad)

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
        wc_sz = sizes["wildcard_size"]
        wc_corner = sizes["wildcard_corner_radius"]
        wc_gap = sizes["wildcard_gap"]
        lightning_sz = sizes["lightning_icon"]
        freeze_sz = sizes["freeze_icon"]
        wc_font_size = sizes["wildcard_font"]
        charges_font_size = sizes["charges_font"]

        # Update wildcard buttons
        for btn in [
            self.wildcard_x2_btn,
            self.wildcard_hint_btn,
            self.wildcard_freeze_btn,
        ]:
            if btn and btn.winfo_exists():
                btn.configure(
                    width=wc_sz,
                    height=wc_sz,
                    corner_radius=wc_corner,
                )
                btn.grid_configure(pady=wc_gap)

        # Update lightning icon
        if self.lightning_icon:
            self.lightning_icon.configure(size=(lightning_sz, lightning_sz))

        # Update freeze wildcard icon
        if self.freeze_wildcard_icon:
            self.freeze_wildcard_icon.configure(size=(freeze_sz, freeze_sz))

        # Update wildcards frame padding
        if self.wildcards_frame and self.wildcards_frame.winfo_exists():
            pad_x = self.scale_value(24, scale, 12, 48)
            pad_y = self.scale_value(24, scale, 12, 48)
            self.wildcards_frame.grid_configure(padx=(0, pad_x), pady=pad_y)

        # Update wildcard button fonts
        try:
            wc_font = ctk.CTkFont(
                family="Poppins ExtraBold", size=wc_font_size, weight="bold"
            )
            for btn in [self.wildcard_x2_btn, self.wildcard_hint_btn]:
                if btn and btn.winfo_exists():
                    btn.configure(font=wc_font)
        except Exception:
            pass

        # Update charges label font
        if self.charges_label and self.charges_label.winfo_exists():
            try:
                charges_font = ctk.CTkFont(
                    family="Poppins SemiBold", size=charges_font_size, weight="bold"
                )
                self.charges_label.configure(font=charges_font)
            except Exception:
                pass

        # Update multiplier label font
        if self.multiplier_label and self.multiplier_label.winfo_exists():
            mul_font_size = self.scale_value(20, scale, 12, 36)
            try:
                mul_font = ctk.CTkFont(
                    family="Poppins ExtraBold", size=mul_font_size, weight="bold"
                )
                self.multiplier_label.configure(font=mul_font)
            except Exception:
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

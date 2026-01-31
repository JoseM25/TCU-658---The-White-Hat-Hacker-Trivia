import tkinter as tk
from tkinter import messagebox
from types import SimpleNamespace

from juego.pantalla_preguntas_config import QuestionPersistenceError
from juego.pantalla_preguntas_ui import QuestionScreenUIMixin
from juego.preguntas_modales import (
    AddQuestionModal,
    DeleteConfirmationModal,
    EditQuestionModal,
)


class QuestionScreenHandlersMixin(QuestionScreenUIMixin):

    def clear_search(self):
        if self.search_entry and self.search_entry.winfo_exists():
            try:
                self.search_entry.delete(0, tk.END)
            except tk.TclError:
                pass

    def handle_search(self):
        query = self.search_entry.get() if self.search_entry else ""
        self.filter_questions(query)
        self.render_question_list()

    def handle_global_click(self, event):
        if not self.search_entry or not self.search_entry.winfo_exists():
            return

        widget = event.widget
        current_widget = widget
        is_search_entry = False

        while current_widget:
            if current_widget == self.search_entry:
                is_search_entry = True
                break
            try:
                current_widget = current_widget.master
            except (AttributeError, tk.TclError):
                break

        if not is_search_entry:
            self.parent.focus_set()

    def on_question_selected(self, question, button):
        self.tts.stop()

        if not self.detail_visible:
            self.detail_container.grid()
            self.detail_visible = True

        c = self.COLORS
        if (
            self.selected_question_button
            and self.selected_question_button is not button
            and self.selected_question_button.winfo_exists()
        ):
            try:
                self.selected_question_button.configure(
                    fg_color=c["question_bg"],
                    text_color=c["question_text"],
                    hover_color=c["question_hover"],
                )
            except tk.TclError:
                pass

        button.configure(
            fg_color=c["question_selected"],
            text_color=c["text_white"],
            hover_color=c["question_selected"],
        )
        self.selected_question_button = button

        self.current_question = question
        title = question.get("title", "")
        definition = (
            question.get("definition", "").strip() or "No definition available yet."
        )
        image_path = question.get("image", "")

        self.detail_title_label.configure(text=title)
        if (
            self.detail_definition_textbox
            and self.detail_definition_textbox.winfo_exists()
        ):
            self.detail_definition_textbox.configure(state="normal")
            self.detail_definition_textbox.delete("0.0", "end")
            self.detail_definition_textbox.insert("0.0", definition)
            self.detail_definition_textbox.configure(state="disabled")
            self.queue_detail_scroll_update()

        if self.detail_title_label and self.detail_title_label.winfo_exists():
            try:
                self.detail_title_label.after_idle(self.apply_title_wraplength)
            except tk.TclError:
                self.apply_title_wraplength()

        self.update_detail_image(image_path)

        self.definition_audio_button.configure(
            state="normal" if question.get("definition", "").strip() else "disabled"
        )

    def clear_detail_panel(self):
        self.tts.stop()
        self.current_question = None
        self.selected_question_button = None

        if (
            self.detail_visible
            and self.detail_container
            and self.detail_container.winfo_exists()
        ):
            self.detail_container.grid_remove()
            self.detail_visible = False

        self.current_detail_image = None

        if self.detail_title_label and self.detail_title_label.winfo_exists():
            self.detail_title_label.configure(text="")
        if (
            self.detail_definition_textbox
            and self.detail_definition_textbox.winfo_exists()
        ):
            self.detail_definition_textbox.configure(state="normal")
            self.detail_definition_textbox.delete("0.0", "end")
            self.detail_definition_textbox.configure(state="disabled")
            self.queue_detail_scroll_update()
        if self.definition_audio_button and self.definition_audio_button.winfo_exists():
            self.definition_audio_button.configure(state="disabled")

        if self.detail_image_label and self.detail_image_label.winfo_exists():
            try:
                self.detail_image_label.configure(
                    image=self.detail_image_placeholder, text="Image placeholder"
                )
            except tk.TclError:
                pass

    def update_detail_image(self, image_path):
        if not self.detail_image_label or not self.detail_image_label.winfo_exists():
            return

        size = self.size_state.get("detail_image", self.SIZES["detail_image"])
        try:
            self.detail_image_placeholder.configure(size=size)
        except tk.TclError:
            pass

        detail_image = (
            self.image_handler.create_detail_image(image_path, size)
            if image_path
            else None
        )
        self.current_detail_image = detail_image

        fallback_text = ""
        if not detail_image:
            fallback_text = "Image not available" if image_path else "Image placeholder"

        try:
            self.detail_image_label.configure(
                image=detail_image or self.detail_image_placeholder, text=fallback_text
            )
        except tk.TclError:
            pass

    def refresh_detail_image(self):
        image_path = ""
        if self.current_question:
            image_path = self.current_question.get("image", "")
        self.update_detail_image(image_path)

    def render_question_list(self):
        if not self.list_container or not self.list_container.winfo_exists():
            return

        for child in self.list_container.winfo_children():
            child.destroy()

        s = self.size_state
        questions = self.filtered_questions
        search_query = self.search_entry.get() if self.search_entry else ""

        selected_visible = (
            any(q is self.current_question for q in questions)
            if self.current_question
            else False
        )
        if not selected_visible and self.current_question:
            self.clear_detail_panel()

        is_scrollable = len(questions) > s.get(
            "max_questions", self.SIZES["max_questions"]
        )
        list_frame = self.create_list_frame_container(is_scrollable)

        if not questions:
            self.show_empty_list_state(list_frame, search_query.strip())
            return

        button_config = {
            "height": s.get("question_btn_height", self.SIZES["question_btn_height"]),
            "corner_radius": s.get(
                "question_corner_radius", self.SIZES["question_corner_radius"]
            ),
        }
        button_margin = s.get("question_margin", self.SIZES["question_margin"])
        button_padding = s.get("question_padding", self.SIZES["question_padding"])

        self.selected_question_button = None
        first_button = None

        for index, question in enumerate(questions, start=0):
            is_selected = selected_visible and question is self.current_question

            button = self.create_question_button(
                list_frame, question, is_selected, button_config
            )

            btn_padx = button_margin
            if is_scrollable:
                offset = s.get("scrollbar_offset", 22)
                btn_padx = (button_margin, button_margin + offset)

            button.grid(
                row=index,
                column=0,
                sticky="nsew",
                padx=btn_padx,
                pady=button_padding,
            )

            if first_button is None:
                first_button = button

            if is_selected:
                self.selected_question_button = button

        if not self.current_question and first_button:
            self.on_question_selected(questions[0], first_button)
            return

        if (
            self.current_question
            and self.selected_question_button
            and not self.detail_visible
        ):
            self.on_question_selected(
                self.current_question, self.selected_question_button
            )

    def queue_detail_scroll_update(self):
        if not self.parent or not self.parent.winfo_exists():
            return
        if self.detail_scroll_update_job:
            try:
                self.parent.after_cancel(self.detail_scroll_update_job)
            except tk.TclError:
                pass
            self.detail_scroll_update_job = None
        try:
            self.detail_scroll_update_job = self.parent.after_idle(
                self.update_detail_scrollbar_visibility
            )
        except tk.TclError:
            self.detail_scroll_update_job = None
            self.update_detail_scrollbar_visibility()

    def update_detail_scrollbar_visibility(self):
        self.detail_scroll_update_job = None
        textbox = self.detail_definition_textbox
        if not textbox or not textbox.winfo_exists():
            return

        scrollbar = self.get_textbox_scrollbar(textbox)
        if not scrollbar or not scrollbar.winfo_exists():
            return

        target = self.get_textbox_scroll_target(textbox)
        if not target:
            return

        try:
            textbox.update_idletasks()
            _, last = target.yview()
        except (tk.TclError, AttributeError, TypeError, ValueError):
            return

        needs_scroll = last < 0.999
        self.set_detail_scrollbar_visible(needs_scroll)

    def set_detail_scrollbar_visible(self, visible):
        if self.detail_scrollbar_visible is visible:
            return

        scrollbar = self.get_textbox_scrollbar(self.detail_definition_textbox)
        if not scrollbar or not scrollbar.winfo_exists():
            return

        manager = self.detail_scrollbar_manager or scrollbar.winfo_manager()
        if not manager:
            manager = "grid"
        self.detail_scrollbar_manager = manager

        if visible:
            if manager == "grid":
                scrollbar.grid()
            elif manager == "pack":
                scrollbar.pack()
            elif manager == "place":
                scrollbar.place()
        else:
            if manager == "grid":
                scrollbar.grid_remove()
            elif manager == "pack":
                scrollbar.pack_forget()
            elif manager == "place":
                scrollbar.place_forget()

        self.detail_scrollbar_visible = visible

    def get_textbox_scrollbar(self, textbox):
        if not textbox:
            return None
        for attr in (
            "_scrollbar",
            "_scrollbar_vertical",
            "_y_scrollbar",
            "_scrollbar_y",
        ):
            scrollbar = getattr(textbox, attr, None)
            if scrollbar:
                return scrollbar
        return None

    def get_textbox_scroll_target(self, textbox):
        if not textbox:
            return None
        target = getattr(textbox, "_textbox", None)
        if target and hasattr(target, "yview"):
            return target
        if hasattr(textbox, "yview"):
            return textbox
        return None

    # Manejadores de modales

    def get_standard_modal_keys(self):
        return [
            "BG_LIGHT",
            "BG_WHITE",
            "BG_MODAL_HEADER",
            "BORDER_MEDIUM",
            "PRIMARY_BLUE",
            "PRIMARY_BLUE_HOVER",
            "BUTTON_CANCEL_BG",
            "BUTTON_CANCEL_HOVER",
            "TEXT_DARK",
            "TEXT_WHITE",
            "TEXT_LIGHT",
            "TEXT_ERROR",
            "SUCCESS_GREEN",
            "dialog_title_font",
            "dialog_label_font",
            "body_font",
            "button_font",
            "cancel_button_font",
        ]

    def create_modal_ui_config(self, keys):
        color_map = {
            "BG_LIGHT": "bg_light",
            "BG_WHITE": "bg_white",
            "BG_MODAL_HEADER": "bg_modal",
            "BORDER_MEDIUM": "border_medium",
            "PRIMARY_BLUE": "primary",
            "PRIMARY_BLUE_HOVER": "primary_hover",
            "BUTTON_CANCEL_BG": "btn_cancel",
            "BUTTON_CANCEL_HOVER": "btn_cancel_hover",
            "TEXT_DARK": "text_dark",
            "TEXT_WHITE": "text_white",
            "TEXT_LIGHT": "text_light",
            "TEXT_ERROR": "text_error",
            "SUCCESS_GREEN": "success",
            "DANGER_RED": "danger",
            "DANGER_RED_HOVER": "danger_hover",
        }

        config_dict = {k: self.COLORS[v] for k, v in color_map.items() if k in keys}

        font_keys = [
            "dialog_title_font",
            "dialog_label_font",
            "dialog_body_font",
            "body_font",
            "button_font",
            "cancel_button_font",
        ]
        config_dict.update({k: getattr(self, k) for k in font_keys if k in keys})

        return SimpleNamespace(**config_dict)

    def show_save_error(self, error):
        message = (
            "Unable to update the questions file. "
            f"Please check permissions and try again.\n\nDetails: {error}"
        )
        try:
            messagebox.showerror("Save error", message)
        except tk.TclError:
            print(f"Save error: {message}")

    def on_add_clicked(self):
        ui_config = self.create_modal_ui_config(self.get_standard_modal_keys())
        self.current_modal = AddQuestionModal(
            self.parent, ui_config, self.image_handler, self.handle_add_save
        )
        self.current_modal.show()
        self.resize_current_modal()

    def handle_add_save(self, title, definition, source_image_path):
        if not self.repository.is_title_unique(title):
            messagebox.showwarning(
                "Duplicate Question",
                "A question with this title already exists. Please use a different title.",
            )
            return False

        relative_image_path = self.image_handler.copy_image_to_project(
            source_image_path
        )
        if not relative_image_path:
            return False

        try:
            new_question = self.repository.add_question(
                title, definition, relative_image_path.as_posix()
            )
        except QuestionPersistenceError as error:
            self.show_save_error(error)
            return False

        self.refresh_question_cache()
        self.filtered_questions = list(self.questions)
        self.current_question = new_question
        self.clear_search()
        self.render_question_list()
        if self.selected_question_button:
            self.on_question_selected(new_question, self.selected_question_button)

        return True

    def on_edit_clicked(self):
        if not self.current_question:
            return
        self.tts.stop()
        ui_config = self.create_modal_ui_config(self.get_standard_modal_keys())
        self.current_modal = EditQuestionModal(
            self.parent,
            ui_config,
            self.image_handler,
            self.handle_edit_save,
            question=self.current_question,
        )
        self.current_modal.show()
        self.resize_current_modal()

    def handle_edit_save(self, title, definition, image_path):
        if not self.repository.is_title_unique(
            title, exclude_question=self.current_question
        ):
            messagebox.showwarning(
                "Duplicate Question",
                "A question with this title already exists. Please use a different title.",
            )
            return False

        stored_image_path = image_path
        if hasattr(image_path, "as_posix"):
            relative_image_path = self.image_handler.copy_image_to_project(image_path)
            if not relative_image_path:
                return False
            stored_image_path = relative_image_path.as_posix()

        try:
            updated_question = self.repository.update_question(
                self.current_question, title, definition, stored_image_path
            )
        except QuestionPersistenceError as error:
            self.show_save_error(error)
            return False

        self.refresh_question_cache()
        self.current_question = updated_question
        self.handle_search()
        if self.selected_question_button:
            self.on_question_selected(updated_question, self.selected_question_button)

        return True

    def on_delete_clicked(self):
        if not self.current_question:
            return
        self.tts.stop()

        delete_keys = [
            "BG_LIGHT",
            "BG_MODAL_HEADER",
            "DANGER_RED",
            "DANGER_RED_HOVER",
            "BUTTON_CANCEL_BG",
            "BUTTON_CANCEL_HOVER",
            "TEXT_DARK",
            "TEXT_WHITE",
            "dialog_title_font",
            "dialog_body_font",
            "button_font",
            "cancel_button_font",
        ]
        ui_config = self.create_modal_ui_config(delete_keys)
        self.current_modal = DeleteConfirmationModal(
            self.parent, ui_config, self.handle_delete_confirm
        )
        self.current_modal.show()
        self.resize_current_modal()

    def handle_delete_confirm(self):
        if not self.current_question:
            return

        try:
            deleted = self.repository.delete_question(self.current_question)
        except QuestionPersistenceError as error:
            self.show_save_error(error)
            return

        if deleted:
            self.refresh_question_cache()
            self.clear_detail_panel()
            self.handle_search()

    def on_audio_clicked(self):
        if self.current_question:
            definition = self.current_question.get("definition", "").strip()
            if definition:
                self.tts.speak(definition)

    def return_to_menu(self):
        self.tts.stop()
        if self.on_return_callback:
            self.on_return_callback()

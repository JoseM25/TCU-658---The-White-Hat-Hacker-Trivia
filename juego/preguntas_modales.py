import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk


class BaseQuestionModal:

    def __init__(self, parent, config, image_handler):
        self.parent = parent
        self.config = config
        self.image_handler = image_handler
        self.modal = None
        self.concept_entry = None
        self.definition_textbox = None
        self.image_display_label = None
        self.image_feedback_label = None
        self.selected_image_source_path = None

    def _create_modal_window(self, title):
        root = self.parent.winfo_toplevel() if self.parent else None
        modal_parent = root if root else self.parent

        modal = ctk.CTkToplevel(modal_parent)
        modal.title(title)
        if root:
            modal.transient(root)

        try:
            modal.grab_set()
        except tk.TclError:
            pass

        modal.resizable(False, False)
        modal.configure(fg_color=self.config.BG_LIGHT)
        modal.grid_rowconfigure(0, weight=1)
        modal.grid_columnconfigure(0, weight=1)

        return modal, root

    def _create_container(self, modal):
        container = ctk.CTkFrame(modal, fg_color=self.config.BG_LIGHT, corner_radius=0)
        container.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(1, weight=1)
        return container

    def _create_header(self, container, title):
        header_frame = ctk.CTkFrame(
            container,
            fg_color=self.config.BG_MODAL_HEADER,
            corner_radius=0,
            height=72,
        )
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 24), padx=0)
        header_frame.grid_propagate(False)
        header_frame.grid_columnconfigure(0, weight=1)

        header_label = ctk.CTkLabel(
            header_frame,
            text=title,
            font=self.config.dialog_title_font,
            text_color=self.config.TEXT_WHITE,
            anchor="center",
            justify="center",
        )
        header_label.grid(row=0, column=0, sticky="nsew", padx=24, pady=(28, 12))

    def _create_form_fields(self, container):
        form_frame = ctk.CTkFrame(container, fg_color=self.config.BG_LIGHT)
        form_frame.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 24))
        form_frame.grid_columnconfigure(0, weight=1)

        # Concept field
        ctk.CTkLabel(
            form_frame,
            text="Concept",
            font=self.config.dialog_label_font,
            text_color=self.config.TEXT_DARK,
            anchor="w",
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))

        self.concept_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="Enter concept",
            fg_color=self.config.BG_WHITE,
            text_color=self.config.TEXT_DARK,
            border_color=self.config.BORDER_MEDIUM,
            border_width=2,
            height=44,
            font=self.config.body_font,
            corner_radius=16,
        )
        self.concept_entry.grid(row=1, column=0, sticky="ew", pady=(0, 16))

        # Definition field
        ctk.CTkLabel(
            form_frame,
            text="Definition",
            font=self.config.dialog_label_font,
            text_color=self.config.TEXT_DARK,
            anchor="w",
        ).grid(row=2, column=0, sticky="w", pady=(0, 8))

        self.definition_textbox = ctk.CTkEntry(
            form_frame,
            fg_color=self.config.BG_WHITE,
            text_color=self.config.TEXT_DARK,
            border_color=self.config.BORDER_MEDIUM,
            border_width=2,
            height=44,
            font=self.config.body_font,
            placeholder_text="Enter definition",
            corner_radius=16,
        )
        self.definition_textbox.grid(row=3, column=0, sticky="ew")

        # Image field
        ctk.CTkLabel(
            form_frame,
            text="Illustration",
            font=self.config.dialog_label_font,
            text_color=self.config.TEXT_DARK,
            anchor="w",
        ).grid(row=4, column=0, sticky="w", pady=(16, 8))

        image_input_frame = ctk.CTkFrame(
            form_frame,
            fg_color=self.config.BG_WHITE,
            border_color=self.config.BORDER_MEDIUM,
            border_width=2,
            corner_radius=16,
        )
        image_input_frame.grid(row=5, column=0, sticky="ew")
        image_input_frame.grid_columnconfigure(0, weight=1)

        image_picker_frame = ctk.CTkFrame(image_input_frame, fg_color="transparent")
        image_picker_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=8)
        image_picker_frame.grid_columnconfigure(0, weight=1)

        self.image_display_label = ctk.CTkLabel(
            image_picker_frame,
            text="No image selected",
            font=self.config.body_font,
            text_color=self.config.TEXT_LIGHT,
            anchor="w",
            wraplength=260,
        )
        self.image_display_label.grid(row=0, column=0, sticky="w", padx=(0, 16))

        image_select_button = ctk.CTkButton(
            image_picker_frame,
            text="Choose File",
            font=self.config.button_font,
            fg_color=self.config.PRIMARY_BLUE,
            hover_color=self.config.PRIMARY_BLUE_HOVER,
            command=self._on_select_image,
            width=140,
            height=36,
            corner_radius=14,
        )
        image_select_button.grid(row=0, column=1, sticky="e")

        self.image_feedback_label = ctk.CTkLabel(
            form_frame,
            text="",
            font=self.config.body_font,
            text_color=self.config.TEXT_ERROR,
            anchor="w",
            wraplength=360,
        )
        self.image_feedback_label.grid(row=6, column=0, sticky="w", pady=(8, 0), padx=4)

        return form_frame

    def _create_buttons(self, container, on_save_callback, on_cancel_callback):
        buttons_frame = ctk.CTkFrame(container, fg_color="transparent")
        buttons_frame.grid(row=2, column=0, sticky="ew", pady=(0, 28), padx=20)
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=0)
        buttons_frame.grid_columnconfigure(2, weight=0)
        buttons_frame.grid_columnconfigure(3, weight=1)

        ctk.CTkButton(
            buttons_frame,
            text="Cancel",
            font=self.config.cancel_button_font,
            fg_color=self.config.BUTTON_CANCEL_BG,
            text_color=self.config.TEXT_WHITE,
            hover_color=self.config.BUTTON_CANCEL_HOVER,
            command=on_cancel_callback,
            width=130,
            height=46,
            corner_radius=14,
        ).grid(row=0, column=1, sticky="e", padx=(0, 32))

        ctk.CTkButton(
            buttons_frame,
            text="Save",
            font=self.config.button_font,
            fg_color=self.config.PRIMARY_BLUE,
            hover_color=self.config.PRIMARY_BLUE_HOVER,
            command=on_save_callback,
            width=130,
            height=46,
            corner_radius=14,
        ).grid(row=0, column=2, sticky="w", padx=(32, 0))

    def _position_modal(self, modal, root, width, height):
        modal.update_idletasks()

        screen_width = modal.winfo_screenwidth()
        screen_height = modal.winfo_screenheight()

        if root and root.winfo_width() > 1 and root.winfo_height() > 1:
            root_x = root.winfo_rootx()
            root_y = root.winfo_rooty()
            root_w = root.winfo_width()
            root_h = root.winfo_height()
            pos_x = root_x + max((root_w - width) // 2, 0)
            pos_y = root_y + max((root_h - height) // 2, 0)
        else:
            pos_x = max((screen_width - width) // 2, 0)
            pos_y = max((screen_height - height) // 2, 0)

        modal.geometry(f"{width}x{height}+{pos_x}+{pos_y}")

    def _on_select_image(self):
        if not self.modal or not self.modal.winfo_exists():
            return

        try:
            initial_dir = (
                str(self.image_handler.images_dir)
                if self.image_handler.images_dir.exists()
                else str(Path.home())
            )
        except (OSError, RuntimeError):
            initial_dir = None

        try:
            file_path = filedialog.askopenfilename(
                parent=self.modal,
                title="Select illustration",
                initialdir=initial_dir,
                filetypes=[
                    ("Image files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp"),
                    ("All files", "*.*"),
                ],
            )
        except tk.TclError:
            return

        if not file_path:
            return

        source_path = Path(file_path)

        if not self.image_handler.validate_image_extension(source_path):
            if self.image_feedback_label:
                self.image_feedback_label.configure(
                    text="Unsupported file type. Please choose a PNG or JPG image.",
                    text_color=self.config.TEXT_ERROR,
                )
            if self.image_display_label:
                self.image_display_label.configure(
                    text="No image selected", text_color=self.config.TEXT_LIGHT
                )
            self.selected_image_source_path = None
            return

        display_name = self.image_handler.truncate_filename(source_path.name)

        if self.image_display_label:
            self.image_display_label.configure(
                text=display_name, text_color=self.config.TEXT_DARK
            )

        if self.image_feedback_label:
            self.image_feedback_label.configure(
                text="Image ready to import.",
                text_color=self.config.SUCCESS_GREEN,
            )

        self.selected_image_source_path = str(source_path)

    def _get_form_data(self):
        if not self.concept_entry or not self.concept_entry.winfo_exists():
            return None

        if not self.definition_textbox or not self.definition_textbox.winfo_exists():
            return None

        title = (self.concept_entry.get() or "").strip()
        definition = (self.definition_textbox.get() or "").strip()

        return {"title": title, "definition": definition}

    def close(self):
        if self.modal and self.modal.winfo_exists():
            try:
                self.modal.grab_release()
            except tk.TclError:
                pass
            self.modal.destroy()

        self.modal = None
        self.concept_entry = None
        self.definition_textbox = None
        self.image_display_label = None
        self.image_feedback_label = None
        self.selected_image_source_path = None


class AddQuestionModal(BaseQuestionModal):

    def __init__(self, parent, config, image_handler, on_save_callback):
        super().__init__(parent, config, image_handler)
        self.on_save_callback = on_save_callback

    def show(self):
        if self.modal and self.modal.winfo_exists():
            try:
                self.modal.lift()
                self.modal.focus_force()
            except tk.TclError:
                pass
            return

        modal, root = self._create_modal_window("Add Question")
        self.modal = modal

        container = self._create_container(modal)
        self._create_header(container, "Add Question")
        self._create_form_fields(container)
        self._create_buttons(container, self._handle_save, self.close)

        modal.protocol("WM_DELETE_WINDOW", self.close)
        modal.bind("<Escape>", lambda e: self.close())

        # Calculate modal size and position
        parent_width = (
            root.winfo_width()
            if root and root.winfo_width() > 1
            else modal.winfo_screenwidth()
        )
        parent_height = (
            root.winfo_height()
            if root and root.winfo_height() > 1
            else modal.winfo_screenheight()
        )

        width = min(max(480, int(parent_width * 0.5)), modal.winfo_screenwidth() - 80)
        height = min(
            max(460, int(parent_height * 0.6)), modal.winfo_screenheight() - 80
        )

        self._position_modal(modal, root, width, height)

        try:
            self.concept_entry.focus_set()
        except tk.TclError:
            pass

    def _handle_save(self):
        form_data = self._get_form_data()
        if not form_data:
            return

        title = form_data["title"]
        definition = form_data["definition"]

        if not title:
            messagebox.showwarning(
                "Missing Information", "Please enter a title for the question."
            )
            try:
                self.concept_entry.focus_set()
            except tk.TclError:
                pass
            return

        if not definition:
            messagebox.showwarning(
                "Missing Information", "Please provide a definition for the question."
            )
            try:
                self.definition_textbox.focus_set()
            except tk.TclError:
                pass
            return

        if not self.selected_image_source_path:
            messagebox.showwarning(
                "Missing Information",
                "Please choose an illustration for the question.",
            )
            if self.image_feedback_label:
                self.image_feedback_label.configure(
                    text="Select an image before saving.",
                    text_color=self.config.TEXT_ERROR,
                )
            return

        source_path = Path(self.selected_image_source_path)
        if not source_path.exists():
            messagebox.showerror(
                "Image Not Found",
                "The selected image could not be located. Please choose a different file.",
            )
            if self.image_feedback_label:
                self.image_feedback_label.configure(
                    text="Selected file is no longer available.",
                    text_color=self.config.TEXT_ERROR,
                )
            self.selected_image_source_path = None
            if self.image_display_label:
                self.image_display_label.configure(
                    text="No image selected", text_color=self.config.TEXT_LIGHT
                )
            return

        # Delegate to callback
        if self.on_save_callback:
            self.on_save_callback(title, definition, source_path)


class EditQuestionModal(BaseQuestionModal):

    def __init__(self, parent, config, image_handler, on_save_callback):
        super().__init__(parent, config, image_handler)
        self.on_save_callback = on_save_callback
        self.initial_image_path = None

    def show(self, current_question):
        if self.modal and self.modal.winfo_exists():
            try:
                self.modal.lift()
                self.modal.focus_force()
            except tk.TclError:
                pass
            return

        modal, root = self._create_modal_window("Edit Question")
        self.modal = modal

        container = self._create_container(modal)
        self._create_header(container, "Edit Question")
        self._create_form_fields(container)
        self._create_buttons(container, self._handle_save, self.close)

        # Populate with current values
        current_title = (current_question.get("title") or "").strip()
        current_definition = (current_question.get("definition") or "").strip()
        existing_image_path = (current_question.get("image") or "").strip()

        if current_title:
            try:
                self.concept_entry.insert(0, current_title)
            except tk.TclError:
                pass

        if current_definition:
            try:
                self.definition_textbox.insert(0, current_definition)
            except tk.TclError:
                pass

        # Update image display
        if existing_image_path:
            try:
                display_source = Path(existing_image_path).name or existing_image_path
            except OSError:
                display_source = existing_image_path

            display_name = self.image_handler.truncate_filename(display_source)
            self.image_display_label.configure(
                text=display_name, text_color=self.config.TEXT_DARK
            )
            self.image_feedback_label.configure(
                text="Current image will be kept unless you choose a new file.",
                text_color=self.config.TEXT_LIGHT,
            )

        self.initial_image_path = existing_image_path

        modal.protocol("WM_DELETE_WINDOW", self.close)
        modal.bind("<Escape>", lambda e: self.close())

        # Calculate modal size and position
        parent_width = (
            root.winfo_width()
            if root and root.winfo_width() > 1
            else modal.winfo_screenwidth()
        )
        parent_height = (
            root.winfo_height()
            if root and root.winfo_height() > 1
            else modal.winfo_screenheight()
        )

        width = min(max(480, int(parent_width * 0.5)), modal.winfo_screenwidth() - 80)
        height = min(
            max(460, int(parent_height * 0.6)), modal.winfo_screenheight() - 80
        )

        self._position_modal(modal, root, width, height)

        try:
            self.concept_entry.focus_set()
        except tk.TclError:
            pass

    def _handle_save(self):
        form_data = self._get_form_data()
        if not form_data:
            return

        title = form_data["title"]
        definition = form_data["definition"]

        if not title:
            messagebox.showwarning(
                "Missing Information", "Please enter a title for the question."
            )
            try:
                self.concept_entry.focus_set()
            except tk.TclError:
                pass
            return

        if not definition:
            messagebox.showwarning(
                "Missing Information", "Please provide a definition for the question."
            )
            try:
                self.definition_textbox.focus_set()
            except tk.TclError:
                pass
            return

        # Determine image path
        image_path = self.initial_image_path or ""

        if self.selected_image_source_path:
            source_path = Path(self.selected_image_source_path)
            if not source_path.exists():
                messagebox.showerror(
                    "Image Not Found",
                    "The selected image could not be located.",
                )
                if self.image_feedback_label:
                    self.image_feedback_label.configure(
                        text="Selected file is no longer available.",
                        text_color=self.config.TEXT_ERROR,
                    )
                return

            if not self.image_handler.validate_image_extension(source_path):
                messagebox.showwarning(
                    "Unsupported File",
                    "Please choose a PNG or JPG image.",
                )
                return

            # Will be processed by callback
            image_path = source_path

        # Delegate to callback
        if self.on_save_callback:
            self.on_save_callback(title, definition, image_path)

    def close(self):
        super().close()
        self.initial_image_path = None


class DeleteConfirmationModal:

    def __init__(self, parent, config, on_confirm_callback):
        self.parent = parent
        self.config = config
        self.on_confirm_callback = on_confirm_callback
        self.modal = None

    def show(self):
        if self.modal and self.modal.winfo_exists():
            try:
                self.modal.lift()
                self.modal.focus_force()
            except tk.TclError:
                pass
            return

        root = self.parent.winfo_toplevel() if self.parent else None
        modal_parent = root if root else self.parent

        modal = ctk.CTkToplevel(modal_parent)
        modal.title("Delete Question")
        if root:
            modal.transient(root)

        try:
            modal.grab_set()
        except tk.TclError:
            pass

        modal.resizable(False, False)
        modal.configure(fg_color=self.config.BG_LIGHT)
        modal.grid_rowconfigure(0, weight=1)
        modal.grid_columnconfigure(0, weight=1)

        container = ctk.CTkFrame(modal, fg_color=self.config.BG_LIGHT, corner_radius=0)
        container.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(1, weight=1)

        # Header
        header_frame = ctk.CTkFrame(
            container,
            fg_color=self.config.BG_MODAL_HEADER,
            corner_radius=0,
            height=72,
        )
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 24), padx=0)
        header_frame.grid_propagate(False)
        header_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header_frame,
            text="Delete Question",
            font=self.config.dialog_title_font,
            text_color=self.config.TEXT_WHITE,
            anchor="center",
        ).grid(row=0, column=0, sticky="nsew", padx=24, pady=(28, 12))

        # Message
        message_label = ctk.CTkLabel(
            container,
            text="Are you sure you want to delete this question? This action is irreversible.",
            font=self.config.dialog_body_font,
            text_color=self.config.TEXT_DARK,
            justify="center",
            anchor="center",
            wraplength=480,
        )
        message_label.grid(row=1, column=0, sticky="nsew", pady=(0, 20), padx=20)

        # Buttons
        buttons_frame = ctk.CTkFrame(container, fg_color="transparent")
        buttons_frame.grid(row=2, column=0, sticky="ew", pady=(0, 28), padx=20)
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=0)
        buttons_frame.grid_columnconfigure(2, weight=0)
        buttons_frame.grid_columnconfigure(3, weight=1)

        ctk.CTkButton(
            buttons_frame,
            text="Cancel",
            font=self.config.cancel_button_font,
            fg_color=self.config.BUTTON_CANCEL_BG,
            text_color=self.config.TEXT_WHITE,
            hover_color=self.config.BUTTON_CANCEL_HOVER,
            command=self.close,
            width=130,
            height=46,
            corner_radius=14,
        ).grid(row=0, column=1, sticky="e", padx=(0, 32))

        confirm_button = ctk.CTkButton(
            buttons_frame,
            text="Delete",
            font=self.config.button_font,
            fg_color=self.config.DANGER_RED,
            hover_color=self.config.DANGER_RED_HOVER,
            command=self._handle_confirm,
            width=130,
            height=46,
            corner_radius=14,
        )
        confirm_button.grid(row=0, column=2, sticky="w", padx=(32, 0))

        self.modal = modal
        modal.protocol("WM_DELETE_WINDOW", self.close)
        modal.bind("<Escape>", lambda e: self.close())

        # Position modal
        modal.update_idletasks()
        screen_width = modal.winfo_screenwidth()
        screen_height = modal.winfo_screenheight()

        parent_width = (
            root.winfo_width() if root and root.winfo_width() > 1 else screen_width
        )
        parent_height = (
            root.winfo_height() if root and root.winfo_height() > 1 else screen_height
        )

        width = min(max(480, int(parent_width * 0.5)), screen_width - 80)
        height = min(max(340, int(parent_height * 0.5)), screen_height - 80)

        if root and root.winfo_width() > 1 and root.winfo_height() > 1:
            root_x = root.winfo_rootx()
            root_y = root.winfo_rooty()
            root_w = root.winfo_width()
            root_h = root.winfo_height()
            pos_x = root_x + max((root_w - width) // 2, 0)
            pos_y = root_y + max((root_h - height) // 2, 0)
        else:
            pos_x = max((screen_width - width) // 2, 0)
            pos_y = max((screen_height - height) // 2, 0)

        modal.geometry(f"{width}x{height}+{pos_x}+{pos_y}")
        message_label.configure(wraplength=max(width - 120, 360))

        try:
            confirm_button.focus_set()
        except tk.TclError:
            pass

    def _handle_confirm(self):
        if self.on_confirm_callback:
            self.on_confirm_callback()

    def close(self):
        if self.modal and self.modal.winfo_exists():
            try:
                self.modal.grab_release()
            except tk.TclError:
                pass
            try:
                self.modal.destroy()
            except tk.TclError:
                pass

        self.modal = None

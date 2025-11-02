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

    def safe_try(self, func):
        try:
            func()
        except tk.TclError:
            pass

    def create_label(self, parent, text, **kwargs):
        defaults = {
            "font": self.config.dialog_label_font,
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
            "height": 44,
            "font": self.config.body_font,
            "corner_radius": 16,
        }
        return ctk.CTkEntry(
            parent, placeholder_text=placeholder, **{**defaults, **kwargs}
        )

    def create_button(self, parent, text, command, is_primary=True, **kwargs):
        if is_primary:
            defaults = {
                "font": self.config.button_font,
                "fg_color": self.config.PRIMARY_BLUE,
                "hover_color": self.config.PRIMARY_BLUE_HOVER,
                "width": 130,
                "height": 46,
                "corner_radius": 14,
            }
        else:
            defaults = {
                "font": self.config.cancel_button_font,
                "fg_color": self.config.BUTTON_CANCEL_BG,
                "text_color": self.config.TEXT_WHITE,
                "hover_color": self.config.BUTTON_CANCEL_HOVER,
                "width": 130,
                "height": 46,
                "corner_radius": 14,
            }
        return ctk.CTkButton(
            parent, text=text, command=command, **{**defaults, **kwargs}
        )

    def create_modal_window(self, title):
        root = self.parent.winfo_toplevel() if self.parent else None
        modal = ctk.CTkToplevel(root if root else self.parent)
        modal.title(title)
        if root:
            modal.transient(root)
        self.safe_try(modal.grab_set)
        modal.resizable(False, False)
        modal.configure(fg_color=self.config.BG_LIGHT)
        modal.grid_rowconfigure(0, weight=1)
        modal.grid_columnconfigure(0, weight=1)
        return modal, root

    def create_container(self, modal):
        container = ctk.CTkFrame(modal, fg_color=self.config.BG_LIGHT, corner_radius=0)
        container.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(1, weight=1)
        return container

    def create_header(self, container, title):
        header_frame = ctk.CTkFrame(
            container, fg_color=self.config.BG_MODAL_HEADER, corner_radius=0, height=72
        )
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 24), padx=0)
        header_frame.grid_propagate(False)
        header_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header_frame,
            text=title,
            font=self.config.dialog_title_font,
            text_color=self.config.TEXT_WHITE,
            anchor="center",
            justify="center",
        ).grid(row=0, column=0, sticky="nsew", padx=24, pady=(28, 12))

    def create_form_fields(self, container):
        form_frame = ctk.CTkFrame(container, fg_color=self.config.BG_LIGHT)
        form_frame.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 24))
        form_frame.grid_columnconfigure(0, weight=1)

        # Concept field
        self.create_label(form_frame, "Concept").grid(
            row=0, column=0, sticky="w", pady=(0, 8)
        )
        self.concept_entry = self.create_entry(form_frame, "Enter concept")
        self.concept_entry.grid(row=1, column=0, sticky="ew", pady=(0, 16))

        # Definition field
        self.create_label(form_frame, "Definition").grid(
            row=2, column=0, sticky="w", pady=(0, 8)
        )
        self.definition_textbox = self.create_entry(form_frame, "Enter definition")
        self.definition_textbox.grid(row=3, column=0, sticky="ew")

        # Image field
        self.create_label(form_frame, "Illustration").grid(
            row=4, column=0, sticky="w", pady=(16, 8)
        )

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

        self.create_button(
            image_picker_frame,
            "Choose File",
            self.on_select_image,
            width=140,
            height=36,
        ).grid(row=0, column=1, sticky="e")

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

    def create_buttons(self, container, on_save_callback, on_cancel_callback):
        buttons_frame = ctk.CTkFrame(container, fg_color="transparent")
        buttons_frame.grid(row=2, column=0, sticky="ew", pady=(0, 28), padx=20)
        for i in range(4):
            buttons_frame.grid_columnconfigure(i, weight=1 if i in (0, 3) else 0)

        self.create_button(
            buttons_frame, "Cancel", on_cancel_callback, is_primary=False
        ).grid(row=0, column=1, sticky="e", padx=(0, 32))
        self.create_button(buttons_frame, "Save", on_save_callback).grid(
            row=0, column=2, sticky="w", padx=(32, 0)
        )

    def calculate_modal_dimensions(
        self,
        modal,
        root,
        width_ratio=0.5,
        height_ratio=0.6,
        min_width=480,
        min_height=460,
    ):
        screen_width = modal.winfo_screenwidth()
        screen_height = modal.winfo_screenheight()

        parent_width = (
            root.winfo_width() if root and root.winfo_width() > 1 else screen_width
        )
        parent_height = (
            root.winfo_height() if root and root.winfo_height() > 1 else screen_height
        )

        width = min(max(min_width, int(parent_width * width_ratio)), screen_width - 80)
        height = min(
            max(min_height, int(parent_height * height_ratio)), screen_height - 80
        )
        return width, height

    def position_modal(self, modal, root, width, height):
        modal.update_idletasks()
        screen_width, screen_height = (
            modal.winfo_screenwidth(),
            modal.winfo_screenheight(),
        )

        if root and root.winfo_width() > 1 and root.winfo_height() > 1:
            pos_x = root.winfo_rootx() + max((root.winfo_width() - width) // 2, 0)
            pos_y = root.winfo_rooty() + max((root.winfo_height() - height) // 2, 0)
        else:
            pos_x = max((screen_width - width) // 2, 0)
            pos_y = max((screen_height - height) // 2, 0)

        modal.geometry(f"{width}x{height}+{pos_x}+{pos_y}")

    def update_image_feedback(self, message, is_error=True):
        if self.image_feedback_label:
            color = self.config.TEXT_ERROR if is_error else self.config.SUCCESS_GREEN
            self.image_feedback_label.configure(text=message, text_color=color)

    def reset_image_display(self):
        if self.image_display_label:
            self.image_display_label.configure(
                text="No image selected", text_color=self.config.TEXT_LIGHT
            )
        self.selected_image_source_path = None

    def on_select_image(self):
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
            self.update_image_feedback(
                "Unsupported file type. Please choose a PNG or JPG image."
            )
            self.reset_image_display()
            return

        display_name = self.image_handler.truncate_filename(source_path.name)
        if self.image_display_label:
            self.image_display_label.configure(
                text=display_name, text_color=self.config.TEXT_DARK
            )
        self.update_image_feedback("Image ready to import.", is_error=False)
        self.selected_image_source_path = str(source_path)

    def get_form_data(self):
        if not self.concept_entry or not self.concept_entry.winfo_exists():
            return None
        if not self.definition_textbox or not self.definition_textbox.winfo_exists():
            return None

        return {
            "title": (self.concept_entry.get() or "").strip(),
            "definition": (self.definition_textbox.get() or "").strip(),
        }

    def close(self):
        if self.modal and self.modal.winfo_exists():
            self.safe_try(self.modal.grab_release)
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
        if self.show_existing_modal():
            return

        modal, root = self.create_modal_window("Add Question")
        self.modal = modal

        self.setup_modal_ui(modal, "Add Question")
        width, height = self.calculate_modal_dimensions(modal, root, 0.5, 0.6, 480, 460)
        self.position_modal(modal, root, width, height)
        self.safe_try(self.concept_entry.focus_set)

    def show_existing_modal(self):
        if self.modal and self.modal.winfo_exists():
            self.safe_try(lambda: (self.modal.lift(), self.modal.focus_force()))
            return True
        return False

    def setup_modal_ui(self, modal, title):
        container = self.create_container(modal)
        self.create_header(container, title)
        self.create_form_fields(container)
        self.create_buttons(container, self.handle_save, self.close)
        modal.protocol("WM_DELETE_WINDOW", self.close)
        modal.bind("<Escape>", lambda e: self.close())

    def validate_field(self, value, field_name, widget):
        if not value:
            messagebox.showwarning(
                "Missing Information", f"Please enter a {field_name} for the question."
            )
            self.safe_try(widget.focus_set)
            return False
        return True

    def handle_save(self):
        form_data = self.get_form_data()
        if not form_data:
            return

        title, definition = form_data["title"], form_data["definition"]

        if not self.validate_field(title, "title", self.concept_entry):
            return
        if not self.validate_field(definition, "definition", self.definition_textbox):
            return

        if not self.selected_image_source_path:
            messagebox.showwarning(
                "Missing Information", "Please choose an illustration for the question."
            )
            self.update_image_feedback("Select an image before saving.")
            return

        source_path = Path(self.selected_image_source_path)
        if not source_path.exists():
            messagebox.showerror(
                "Image Not Found",
                "The selected image could not be located. Please choose a different file.",
            )
            self.update_image_feedback("Selected file is no longer available.")
            self.reset_image_display()
            return

        if self.on_save_callback:
            self.on_save_callback(title, definition, source_path)


class EditQuestionModal(BaseQuestionModal):

    def __init__(self, parent, config, image_handler, on_save_callback):
        super().__init__(parent, config, image_handler)
        self.on_save_callback = on_save_callback
        self.initial_image_path = None

    def show(self, current_question):
        if self.show_existing_modal():
            return

        modal, root = self.create_modal_window("Edit Question")
        self.modal = modal

        self.setup_modal_ui(modal, "Edit Question")
        self.populate_form(current_question)

        width, height = self.calculate_modal_dimensions(modal, root, 0.5, 0.6, 480, 460)
        self.position_modal(modal, root, width, height)
        self.safe_try(self.concept_entry.focus_set)

    def show_existing_modal(self):
        if self.modal and self.modal.winfo_exists():
            self.safe_try(lambda: (self.modal.lift(), self.modal.focus_force()))
            return True
        return False

    def setup_modal_ui(self, modal, title):
        container = self.create_container(modal)
        self.create_header(container, title)
        self.create_form_fields(container)
        self.create_buttons(container, self.handle_save, self.close)
        modal.protocol("WM_DELETE_WINDOW", self.close)
        modal.bind("<Escape>", lambda e: self.close())

    def populate_form(self, current_question):
        current_title = (current_question.get("title") or "").strip()
        current_definition = (current_question.get("definition") or "").strip()
        existing_image_path = (current_question.get("image") or "").strip()

        if current_title:
            self.safe_try(lambda: self.concept_entry.insert(0, current_title))
        if current_definition:
            self.safe_try(lambda: self.definition_textbox.insert(0, current_definition))

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

    def validate_field(self, value, field_name, widget):
        if not value:
            messagebox.showwarning(
                "Missing Information", f"Please enter a {field_name} for the question."
            )
            self.safe_try(widget.focus_set)
            return False
        return True

    def handle_save(self):
        form_data = self.get_form_data()
        if not form_data:
            return

        title, definition = form_data["title"], form_data["definition"]

        if not self.validate_field(title, "title", self.concept_entry):
            return
        if not self.validate_field(definition, "definition", self.definition_textbox):
            return

        image_path = self.initial_image_path or ""

        if self.selected_image_source_path:
            source_path = Path(self.selected_image_source_path)
            if not source_path.exists():
                messagebox.showerror(
                    "Image Not Found", "The selected image could not be located."
                )
                self.update_image_feedback("Selected file is no longer available.")
                return

            if not self.image_handler.validate_image_extension(source_path):
                messagebox.showwarning(
                    "Unsupported File", "Please choose a PNG or JPG image."
                )
                return

            image_path = source_path

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

    def safe_try(self, func):
        try:
            func()
        except tk.TclError:
            pass

    def calculate_position(self, modal, root, width, height):
        screen_width, screen_height = (
            modal.winfo_screenwidth(),
            modal.winfo_screenheight(),
        )

        if root and root.winfo_width() > 1 and root.winfo_height() > 1:
            pos_x = root.winfo_rootx() + max((root.winfo_width() - width) // 2, 0)
            pos_y = root.winfo_rooty() + max((root.winfo_height() - height) // 2, 0)
        else:
            pos_x = max((screen_width - width) // 2, 0)
            pos_y = max((screen_height - height) // 2, 0)
        return pos_x, pos_y

    def show(self):
        if self.modal and self.modal.winfo_exists():
            self.safe_try(lambda: (self.modal.lift(), self.modal.focus_force()))
            return

        root = self.parent.winfo_toplevel() if self.parent else None
        modal = ctk.CTkToplevel(root if root else self.parent)
        modal.title("Delete Question")
        if root:
            modal.transient(root)
        self.safe_try(modal.grab_set)
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
            container, fg_color=self.config.BG_MODAL_HEADER, corner_radius=0, height=72
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
        for i in range(4):
            buttons_frame.grid_columnconfigure(i, weight=1 if i in (0, 3) else 0)

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
            command=self.handle_confirm,
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
        screen_width, screen_height = (
            modal.winfo_screenwidth(),
            modal.winfo_screenheight(),
        )
        parent_width = (
            root.winfo_width() if root and root.winfo_width() > 1 else screen_width
        )
        parent_height = (
            root.winfo_height() if root and root.winfo_height() > 1 else screen_height
        )

        width = min(max(480, int(parent_width * 0.5)), screen_width - 80)
        height = min(max(340, int(parent_height * 0.5)), screen_height - 80)

        pos_x, pos_y = self.calculate_position(modal, root, width, height)
        modal.geometry(f"{width}x{height}+{pos_x}+{pos_y}")
        message_label.configure(wraplength=max(width - 120, 360))

        self.safe_try(confirm_button.focus_set)

    def handle_confirm(self):
        if self.on_confirm_callback:
            self.on_confirm_callback()

    def close(self):
        if self.modal and self.modal.winfo_exists():
            self.safe_try(self.modal.grab_release)
            self.safe_try(self.modal.destroy)
        self.modal = None

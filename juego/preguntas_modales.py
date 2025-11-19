import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from juego.responsive_helpers import ResponsiveScaler
from juego.widget_factory import (
    ModalWidgetFactory,
    ModalLayoutBuilder,
    ScaledWidgetResizer,
)

TITLE_MAX_LENGTH = 50


class QuestionFormMode:

    __slots__ = ("title", "requires_image", "existing_image_hint")

    def __init__(self, title, requires_image, existing_image_hint=""):
        self.title = title
        self.requires_image = requires_image
        self.existing_image_hint = existing_image_hint

    def __repr__(self):
        return (
            f"QuestionFormMode(title={self.title!r}, requires_image={self.requires_image}, "
            f"existing_image_hint={self.existing_image_hint!r})"
        )


class BaseModal:

    BASE_DIMENSIONS = (1280, 720)

    def __init__(self, parent, config):
        self.parent = parent
        self.config = config
        self.modal = None
        self.fonts = {}
        self.font_base_sizes = {}

        # Initialize responsive helpers
        self.scaler = ResponsiveScaler(
            base_dimensions=self.BASE_DIMENSIONS,
            scale_limits=(0.5, 2.0),
            global_scale_factor=1.0,
        )

    def init_fonts(self, font_specs):
        for name, (family, size, weight) in font_specs.items():
            font = (
                ctk.CTkFont(family=family, size=size, weight=weight)
                if weight
                else ctk.CTkFont(family=family, size=size)
            )
            self.fonts[name] = font
            self.font_base_sizes[name] = size

    def update_fonts(self, scale):
        for name, base_size in self.font_base_sizes.items():
            if name in self.fonts:
                new_size = self.scaler.scale_value(base_size, scale, 10, base_size * 2)
                self.fonts[name].configure(size=new_size)

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

    def get_responsive_scale(self, root, base_sizes=None):
        if not root:
            return 1.0

        parent_width = root.winfo_width()
        parent_height = root.winfo_height()
        base_w, base_h = self.BASE_DIMENSIONS

        # Calculate raw scale
        scale = min(parent_width / base_w, parent_height / base_h)

        # Apply boost for lower resolutions to ensure usability
        if base_sizes and parent_height <= 500:
            target_height = parent_height * 0.85
            target_scale = target_height / base_sizes["height"]
            scale = max(scale, target_scale)
        elif base_sizes and parent_height <= 600:
            target_height = parent_height * 0.75
            target_scale = target_height / base_sizes["height"]
            scale = max(scale, target_scale)

        return scale

    def close(self):
        if self.modal and self.modal.winfo_exists():
            self.safe_try(self.modal.grab_release)
            self.safe_try(self.modal.destroy)
        self.modal = None


class BaseQuestionModal(BaseModal):

    BASE_SIZES = {
        "width": 480,
        "height": 360,
        "header_height": 52,
        "padding_x": 14,
        "padding_y": 14,
        "button_width": 110,
        "button_height": 36,
        "entry_height": 36,
        "image_button_width": 110,
        "image_button_height": 28,
        "corner_radius": 12,
        "button_corner_radius": 10,
    }

    FONT_SPECS = {
        "dialog_title": ("Poppins SemiBold", 24, "bold"),
        "dialog_label": ("Poppins SemiBold", 16, "bold"),
        "body": ("Poppins Medium", 14, None),
        "button": ("Poppins SemiBold", 16, "bold"),
        "cancel_button": ("Poppins ExtraBold", 16, "bold"),
    }

    def __init__(self, parent, config, image_handler):
        super().__init__(parent, config)
        self.image_handler = image_handler
        self.concept_entry = None
        self.definition_textbox = None
        self.image_display_label = None
        self.image_feedback_label = None
        self.selected_image_source_path = None
        self.title_var = tk.StringVar()
        self.title_var.trace("w", self.limit_title_length)

        # Initialize fonts
        self.init_fonts(self.FONT_SPECS)

        # Initialize widget factory and helpers
        self.widget_factory = ModalWidgetFactory(config, self.fonts, self.BASE_SIZES)
        self.layout_builder = ModalLayoutBuilder(self.widget_factory)
        self.resizer = ScaledWidgetResizer(self.scaler)

        # Widget references for resizing
        self.header_frame = None
        self.form_frame = None
        self.buttons_frame = None
        self.cancel_button = None
        self.save_button = None
        self.choose_file_button = None
        self.image_input_frame = None
        self.image_picker_frame = None

    def limit_title_length(self, *_):
        value = self.title_var.get()
        if len(value) > TITLE_MAX_LENGTH:
            self.title_var.set(value[:TITLE_MAX_LENGTH])

    def create_label(self, parent, text, **kwargs):
        return self.widget_factory.create_label(parent, text, **kwargs)

    def create_entry(self, parent, placeholder, **kwargs):
        return self.widget_factory.create_entry(parent, placeholder, **kwargs)

    def create_button(self, parent, text, command, is_primary=True, **kwargs):
        return self.widget_factory.create_button(
            parent, text, command, is_primary, **kwargs
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
        return self.layout_builder.create_container(modal, self.config)

    def create_header(self, container, title):
        self.header_frame = self.layout_builder.create_header(
            container, title, self.fonts, self.config
        )

    def create_form_fields(self, container):
        self.form_frame = ctk.CTkFrame(
            container, fg_color="transparent", corner_radius=0
        )
        self.form_frame.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 24))
        self.form_frame.grid_columnconfigure(0, weight=1)

        # Concept field
        self.create_label(self.form_frame, "Concept").grid(
            row=0, column=0, sticky="w", pady=(0, 8)
        )
        self.concept_entry = self.create_entry(
            self.form_frame, "Enter concept", textvariable=self.title_var
        )
        self.concept_entry.grid(row=1, column=0, sticky="ew", pady=(0, 16))

        # Definition field
        self.create_label(self.form_frame, "Definition").grid(
            row=2, column=0, sticky="w", pady=(0, 8)
        )
        self.definition_textbox = self.create_entry(self.form_frame, "Enter definition")
        self.definition_textbox.grid(row=3, column=0, sticky="ew")

        # Image field
        self.create_label(self.form_frame, "Illustration").grid(
            row=4, column=0, sticky="w", pady=(16, 8)
        )

        self.image_input_frame = ctk.CTkFrame(
            self.form_frame,
            fg_color=self.config.BG_WHITE,
            border_color=self.config.BORDER_MEDIUM,
            border_width=2,
            corner_radius=16,
        )
        self.image_input_frame.grid(row=5, column=0, sticky="ew")
        self.image_input_frame.grid_columnconfigure(0, weight=1)

        self.image_picker_frame = ctk.CTkFrame(
            self.image_input_frame, fg_color="transparent"
        )
        self.image_picker_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=8)
        self.image_picker_frame.grid_columnconfigure(0, weight=1)

        self.image_display_label = ctk.CTkLabel(
            self.image_picker_frame,
            text="No image selected",
            font=self.fonts["body"],
            text_color=self.config.TEXT_LIGHT,
            anchor="w",
            wraplength=260,
        )
        self.image_display_label.grid(row=0, column=0, sticky="w", padx=(0, 16))

        self.choose_file_button = self.create_button(
            self.image_picker_frame,
            "Choose File",
            self.on_select_image,
            width=self.BASE_SIZES["image_button_width"],
            height=self.BASE_SIZES["image_button_height"],
        )
        self.choose_file_button.grid(row=0, column=1, sticky="e")

        self.image_feedback_label = ctk.CTkLabel(
            self.form_frame,
            text="",
            font=self.fonts["body"],
            text_color=self.config.TEXT_ERROR,
            anchor="w",
            justify="left",
            wraplength=360,
        )
        self.image_feedback_label.grid(row=6, column=0, sticky="w", pady=(8, 0), padx=4)
        return self.form_frame

    def create_buttons(self, container, on_save_callback, on_cancel_callback):
        self.buttons_frame = ctk.CTkFrame(container, fg_color="transparent")
        self.buttons_frame.grid(row=2, column=0, sticky="ew", pady=(0, 28), padx=20)
        container.grid_rowconfigure(2, weight=0)  # Ensure buttons don't expand
        for i in range(4):
            self.buttons_frame.grid_columnconfigure(i, weight=1 if i in (0, 3) else 0)

        self.cancel_button = self.create_button(
            self.buttons_frame, "Cancel", on_cancel_callback, is_primary=False
        )
        self.cancel_button.grid(row=0, column=1, sticky="e", padx=(0, 32))

        self.save_button = self.create_button(
            self.buttons_frame, "Save", on_save_callback
        )
        self.save_button.grid(row=0, column=2, sticky="w", padx=(32, 0))

    def setup_modal_ui(self, modal, title, on_save_callback, on_cancel_callback=None):
        container = self.create_container(modal)
        self.create_header(container, title)
        self.create_form_fields(container)
        cancel_callback = on_cancel_callback or self.close
        self.create_buttons(container, on_save_callback, cancel_callback)
        modal.protocol("WM_DELETE_WINDOW", cancel_callback)
        modal.bind("<Escape>", lambda e: cancel_callback())
        return container

    def show_existing_modal(self):
        if self.modal and self.modal.winfo_exists():
            self.safe_try(self.modal.lift)
            self.safe_try(self.modal.focus_force)
            return True
        return False

    def open_modal(
        self, title, on_save_callback, after_setup=None, on_cancel_callback=None
    ):
        if self.show_existing_modal():
            return False

        modal, root = self.create_modal_window(title)
        self.modal = modal

        self.setup_modal_ui(
            modal, title, on_save_callback, on_cancel_callback or self.close
        )

        if after_setup:
            after_setup()

        scale = self.get_responsive_scale(root)
        self.resize(scale)
        self.safe_try(self.concept_entry.focus_set)
        return True

    def calculate_modal_dimensions(
        self,
        modal,
        root,
        width_ratio=0.5,
        height_ratio=0.5,
        min_width=480,
        min_height=360,
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
        pos_x, pos_y = self.calculate_position(modal, root, width, height)
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

    def validate_field(self, value, field_name, widget):
        if not value:
            messagebox.showwarning(
                "Missing Information",
                f"Please enter a {field_name} for the question.",
            )
            self.safe_try(widget.focus_set)
            return False
        return True

    def get_validated_form_data(self):
        form_data = self.get_form_data()
        if not form_data:
            return None

        title = form_data["title"]
        definition = form_data["definition"]

        if not self.validate_field(title, "title", self.concept_entry):
            return None
        if not self.validate_field(definition, "definition", self.definition_textbox):
            return None
        return form_data

    def get_responsive_scale(self, root, base_sizes=None):
        return super().get_responsive_scale(root, self.BASE_SIZES)

    def close(self):
        super().close()
        self.concept_entry = None
        self.definition_textbox = None
        self.image_display_label = None
        self.image_feedback_label = None
        self.selected_image_source_path = None

    def resize(self, scale):
        if not self.modal or not self.modal.winfo_exists():
            return

        self.update_fonts(scale)
        s = self.scaler.scale_value

        # Resize modal window
        width = s(self.BASE_SIZES["width"], scale)
        height = s(self.BASE_SIZES["height"], scale)

        # Recalculate position to keep centered
        root = self.parent.winfo_toplevel()
        pos_x, pos_y = self.calculate_position(self.modal, root, width, height)
        self.modal.geometry(f"{width}x{height}+{pos_x}+{pos_y}")

        # Resize header
        if self.header_frame:
            self.header_frame.configure(
                height=s(self.BASE_SIZES["header_height"], scale)
            )
            self.header_frame.grid_configure(
                pady=(0, s(self.BASE_SIZES["padding_y"], scale))
            )

        # Resize form fields container
        if self.form_frame:
            self.form_frame.grid_configure(
                padx=s(self.BASE_SIZES["padding_x"], scale),
                pady=(0, s(self.BASE_SIZES["padding_y"], scale)),
            )

        # Resize buttons frame and buttons
        if self.buttons_frame:
            self.buttons_frame.grid_configure(pady=(0, s(28, scale)), padx=s(20, scale))

        for btn in [self.cancel_button, self.save_button]:
            self.resizer.resize_button(btn, scale, self.BASE_SIZES)

        if self.cancel_button:
            self.cancel_button.grid_configure(padx=(0, s(32, scale)))
        if self.save_button:
            self.save_button.grid_configure(padx=(s(32, scale), 0))

        # Resize entries
        for entry in [self.concept_entry, self.definition_textbox]:
            self.resizer.resize_entry(entry, scale, self.BASE_SIZES)

        if self.concept_entry:
            self.concept_entry.grid_configure(pady=(0, s(16, scale)))

        # Resize image input frame
        if self.image_input_frame:
            self.image_input_frame.configure(
                corner_radius=s(self.BASE_SIZES["corner_radius"], scale)
            )

        if self.image_picker_frame:
            self.image_picker_frame.grid_configure(padx=s(12, scale), pady=s(8, scale))

        if self.choose_file_button:
            self.choose_file_button.configure(
                width=s(self.BASE_SIZES["image_button_width"], scale),
                height=s(self.BASE_SIZES["image_button_height"], scale),
            )

        if self.image_display_label:
            self.image_display_label.grid_configure(padx=(0, s(16, scale)))
            self.image_display_label.configure(wraplength=s(260, scale))

        if self.image_feedback_label:
            self.image_feedback_label.grid_configure(
                pady=(s(8, scale), 0), padx=s(4, scale)
            )
            self.image_feedback_label.configure(wraplength=s(360, scale))


class QuestionFormModal(BaseQuestionModal):

    def __init__(
        self,
        parent,
        config,
        image_handler,
        on_save_callback,
        mode: QuestionFormMode,
        question=None,
    ):
        super().__init__(parent, config, image_handler)
        self.on_save_callback = on_save_callback
        self.mode = mode
        self.question = question
        self.initial_image_path = ""

    def show(self, question=None):
        self.question = question or self.question
        after_setup = None
        if self.question:
            after_setup = lambda: self.populate_form(self.question)
        self.open_modal(self.mode.title, self.handle_save, after_setup=after_setup)

    def populate_form(self, current_question):
        current_title = (current_question.get("title") or "").strip()
        current_definition = (current_question.get("definition") or "").strip()
        existing_image_path = (current_question.get("image") or "").strip()

        if current_title:
            self.title_var.set(current_title)
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
            hint = (
                self.mode.existing_image_hint
                or "Current image will be kept unless you choose a new file."
            )
            self.image_feedback_label.configure(
                text=hint,
                text_color=self.config.TEXT_LIGHT,
            )

        self.initial_image_path = existing_image_path

    def resolve_image_value(self):
        if self.selected_image_source_path:
            source_path = Path(self.selected_image_source_path)
            if not source_path.exists():
                messagebox.showerror(
                    "Image Not Found",
                    "The selected image could not be located. Please choose a different file.",
                )
                self.update_image_feedback("Selected file is no longer available.")
                self.reset_image_display()
                return None

            if not self.image_handler.validate_image_extension(source_path):
                messagebox.showwarning(
                    "Unsupported File", "Please choose a PNG or JPG image."
                )
                self.update_image_feedback("Unsupported file extension.")
                return None

            return source_path

        if self.initial_image_path:
            return self.initial_image_path

        if self.mode.requires_image:
            messagebox.showwarning(
                "Missing Information", "Please choose an illustration for the question."
            )
            self.update_image_feedback("Select an image before saving.")
            return None

        return ""

    def handle_save(self):
        form_data = self.get_validated_form_data()
        if not form_data:
            return

        image_value = self.resolve_image_value()
        if image_value is None:
            return

        if self.on_save_callback:
            result = self.on_save_callback(
                form_data["title"], form_data["definition"], image_value
            )
            if result is False:
                return

        self.close()

    def close(self):
        super().close()
        self.initial_image_path = ""


class AddQuestionModal(QuestionFormModal):

    def __init__(self, parent, config, image_handler, on_save_callback):
        super().__init__(
            parent,
            config,
            image_handler,
            on_save_callback,
            mode=QuestionFormMode(title="Add Question", requires_image=True),
        )


class EditQuestionModal(QuestionFormModal):

    def __init__(self, parent, config, image_handler, on_save_callback, question=None):
        super().__init__(
            parent,
            config,
            image_handler,
            on_save_callback,
            mode=QuestionFormMode(
                title="Edit Question",
                requires_image=False,
                existing_image_hint="Current image will be kept unless you choose a new file.",
            ),
            question=question,
        )


class DeleteConfirmationModal(BaseModal):

    BASE_SIZES = {
        "width": 420,
        "height": 260,
        "header_height": 52,
        "button_width": 110,
        "button_height": 36,
        "button_corner_radius": 10,
    }

    FONT_SPECS = {
        "dialog_title": ("Poppins SemiBold", 24, "bold"),
        "dialog_body": ("Poppins Medium", 16, None),
        "button": ("Poppins SemiBold", 16, "bold"),
        "cancel_button": ("Poppins ExtraBold", 16, "bold"),
    }

    def __init__(self, parent, config, on_confirm_callback):
        super().__init__(parent, config)
        self.on_confirm_callback = on_confirm_callback

        # Initialize fonts
        self.init_fonts(self.FONT_SPECS)

        # Widget references
        self.header_frame = None
        self.message_label = None
        self.buttons_frame = None
        self.cancel_button = None
        self.confirm_button = None

    def get_responsive_scale(self, root, base_sizes=None):
        return super().get_responsive_scale(root, self.BASE_SIZES)

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
        self.header_frame = ctk.CTkFrame(
            container, fg_color=self.config.BG_MODAL_HEADER, corner_radius=0, height=72
        )
        self.header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 24), padx=0)
        self.header_frame.grid_propagate(False)
        self.header_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.header_frame,
            text="Delete Question",
            font=self.fonts["dialog_title"],
            text_color=self.config.TEXT_WHITE,
            anchor="center",
        ).grid(row=0, column=0, sticky="nsew", padx=24, pady=(28, 12))

        # Message
        self.message_label = ctk.CTkLabel(
            container,
            text="Are you sure you want to delete this question? This action is irreversible.",
            font=self.fonts["dialog_body"],
            text_color=self.config.TEXT_DARK,
            justify="center",
            anchor="center",
            wraplength=480,
        )
        self.message_label.grid(row=1, column=0, sticky="nsew", pady=(0, 20), padx=20)

        # Buttons
        self.buttons_frame = ctk.CTkFrame(container, fg_color="transparent")
        self.buttons_frame.grid(row=2, column=0, sticky="ew", pady=(0, 28), padx=20)
        for i in range(4):
            self.buttons_frame.grid_columnconfigure(i, weight=1 if i in (0, 3) else 0)

        self.cancel_button = ctk.CTkButton(
            self.buttons_frame,
            text="Cancel",
            font=self.fonts["cancel_button"],
            fg_color=self.config.BUTTON_CANCEL_BG,
            text_color=self.config.TEXT_WHITE,
            hover_color=self.config.BUTTON_CANCEL_HOVER,
            command=self.close,
            width=130,
            height=46,
            corner_radius=14,
        )
        self.cancel_button.grid(row=0, column=1, sticky="e", padx=(0, 32))

        self.confirm_button = ctk.CTkButton(
            self.buttons_frame,
            text="Delete",
            font=self.fonts["button"],
            fg_color=self.config.DANGER_RED,
            hover_color=self.config.DANGER_RED_HOVER,
            command=self.handle_confirm,
            width=130,
            height=46,
            corner_radius=14,
        )
        self.confirm_button.grid(row=0, column=2, sticky="w", padx=(32, 0))

        self.modal = modal
        modal.protocol("WM_DELETE_WINDOW", self.close)
        modal.bind("<Escape>", lambda e: self.close())

        scale = self.get_responsive_scale(root)
        self.resize(scale)
        self.safe_try(self.confirm_button.focus_set)

    def handle_confirm(self):
        if self.on_confirm_callback:
            self.on_confirm_callback()

        self.close()

    # close() method inherited from BaseModal

    def resize(self, scale):
        if not self.modal or not self.modal.winfo_exists():
            return

        self.update_fonts(scale)
        s = self.scaler.scale_value

        # Resize modal window
        width = s(self.BASE_SIZES["width"], scale)
        height = s(self.BASE_SIZES["height"], scale)

        # Recalculate position to keep centered
        root = self.parent.winfo_toplevel()
        pos_x, pos_y = self.calculate_position(self.modal, root, width, height)
        self.modal.geometry(f"{width}x{height}+{pos_x}+{pos_y}")

        # Resize header
        if self.header_frame:
            self.header_frame.configure(
                height=s(self.BASE_SIZES["header_height"], scale)
            )
            self.header_frame.grid_configure(pady=(0, s(24, scale)))

        # Resize message
        if self.message_label:
            self.message_label.grid_configure(pady=(0, s(20, scale)), padx=s(20, scale))
            self.message_label.configure(
                wraplength=max(width - s(120, scale), s(360, scale))
            )

        # Resize buttons frame
        if self.buttons_frame:
            self.buttons_frame.grid_configure(pady=(0, s(28, scale)), padx=s(20, scale))

        # Resize buttons
        btn_width = s(self.BASE_SIZES["button_width"], scale)
        btn_height = s(self.BASE_SIZES["button_height"], scale)
        btn_radius = s(self.BASE_SIZES["button_corner_radius"], scale)

        for btn in [self.cancel_button, self.confirm_button]:
            if btn:
                btn.configure(
                    width=btn_width, height=btn_height, corner_radius=btn_radius
                )

        if self.cancel_button:
            self.cancel_button.grid_configure(padx=(0, s(32, scale)))
        if self.confirm_button:
            self.confirm_button.grid_configure(padx=(s(32, scale), 0))

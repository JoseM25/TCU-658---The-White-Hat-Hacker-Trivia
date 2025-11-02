import json
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk

from juego.tts_service import TTSService
from juego.image_handler import ImageHandler
from juego.preguntas_modales import (
    AddQuestionModal,
    EditQuestionModal,
    DeleteConfirmationModal,
)


class ManageQuestionsScreen:

    # File and directory paths
    BASE_DIR = Path(__file__).resolve().parent.parent
    QUESTIONS_FILE = BASE_DIR / "datos" / "preguntas.json"
    IMAGES_DIR = BASE_DIR / "recursos" / "imagenes"
    AUDIO_DIR = BASE_DIR / "recursos" / "audio"

    # Icon filenames
    ICONS = {"audio": "volume.svg", "search": "search.svg", "back": "arrow.svg"}

    # UI Colors
    COLORS = {
        "header_bg": "#1C2534",
        "header_hover": "#273246",
        "primary": "#1D6CFF",
        "primary_hover": "#0F55C9",
        "secondary": "#00CFC5",
        "secondary_hover": "#04AFA6",
        "danger": "#FF4F60",
        "danger_hover": "#E53949",
        "success": "#047857",
        "bg_light": "#F5F7FA",
        "bg_white": "#FFFFFF",
        "bg_modal": "#202632",
        "border_light": "#D2DAE6",
        "border_medium": "#CBD5E1",
        "search_bg": "#D1D8E0",
        "text_dark": "#111827",
        "text_medium": "#1F2937",
        "text_light": "#4B5563",
        "text_lighter": "#6B7280",
        "text_white": "#FFFFFF",
        "text_placeholder": "#F5F7FA",
        "text_error": "#DC2626",
        "btn_cancel": "#E5E7EB",
        "btn_cancel_hover": "#CBD5E1",
        "question_bg": "transparent",
        "question_text": "#1F2937",
        "question_hover": "#E2E8F0",
        "question_selected": "#1D6CFF",
    }

    # UI Sizes
    SIZES = {
        "max_questions": 8,
        "detail_image": (220, 220),
        "audio_icon": (32, 32),
        "search_icon": (16, 16),
        "back_icon": (20, 20),
        "question_btn_height": 50,
        "question_margin": 8,
        "question_padding": 4,
        "question_corner_radius": 12,
    }

    def __init__(self, parent, on_return_callback=None):
        self.parent = parent
        self.on_return_callback = on_return_callback

        # Declare font attributes (set in init_fonts)
        self.title_font = None
        self.body_font = None
        self.button_font = None
        self.cancel_button_font = None
        self.search_font = None
        self.question_font = None
        self.detail_title_font = None
        self.dialog_title_font = None
        self.dialog_body_font = None
        self.dialog_label_font = None

        # Initialize fonts
        self.init_fonts()

        # Initialize services
        self.tts = TTSService(self.AUDIO_DIR)
        self.image_handler = ImageHandler(self.IMAGES_DIR)

        # Question management state
        self.questions = []
        self.filtered_questions = []
        self.load_questions()

        # UI State
        self.current_question = None
        self.selected_question_button = None
        self.detail_visible = False

        # UI Components (initialized in build_ui)
        self.search_entry = None
        self.list_container = None
        self.detail_container = None
        self.detail_title_label = None
        self.detail_definition_label = None
        self.detail_image_label = None
        self.definition_audio_button = None

        # Cache icons
        self.detail_image_placeholder = (
            self.image_handler.create_transparent_placeholder()
        )
        self.audio_icon = self.image_handler.create_ctk_icon(
            self.ICONS["audio"], self.SIZES["audio_icon"]
        )
        self.search_icon = self.image_handler.create_ctk_icon(
            self.ICONS["search"], self.SIZES["search_icon"]
        )
        self.back_arrow_icon = self.image_handler.create_ctk_icon(
            self.ICONS["back"], self.SIZES["back_icon"]
        )

        # Clear parent and build UI
        for widget in self.parent.winfo_children():
            widget.destroy()
        self.build_ui()

    def init_fonts(self):
        font_specs = {
            "title": ("Poppins ExtraBold", 38, "bold"),
            "body": ("Poppins Medium", 18, None),
            "button": ("Poppins SemiBold", 16, "bold"),
            "cancel_button": ("Poppins ExtraBold", 16, "bold"),
            "search": ("Poppins SemiBold", 18, "bold"),
            "question": ("Poppins SemiBold", 18, "bold"),
            "detail_title": ("Poppins ExtraBold", 38, "bold"),
            "dialog_title": ("Poppins SemiBold", 24, "bold"),
            "dialog_body": ("Poppins Medium", 16, None),
            "dialog_label": ("Poppins SemiBold", 16, "bold"),
        }
        for name, (family, size, weight) in font_specs.items():
            setattr(
                self,
                f"{name}_font",
                (
                    ctk.CTkFont(family=family, size=size, weight=weight)
                    if weight
                    else ctk.CTkFont(family=family, size=size)
                ),
            )

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

        return type("UIConfig", (), config_dict)()

    def load_questions(self):
        if not self.QUESTIONS_FILE.exists():
            self.questions = self.filtered_questions = []
            return

        try:
            data = json.loads(self.QUESTIONS_FILE.read_text(encoding="utf-8"))
            raw_questions = data.get("questions", []) if hasattr(data, "get") else data
        except json.JSONDecodeError:
            self.questions = self.filtered_questions = []
            return
        except (AttributeError, TypeError):
            raw_questions = data if data else []

        self.questions = [
            {"title": title, "definition": definition, "image": image}
            for item in raw_questions
            if hasattr(item, "get") and (title := (item.get("title") or "").strip())
            for definition in [(item.get("definition") or "").strip()]
            for image in [(item.get("image") or "").strip()]
        ]
        self.filtered_questions = list(self.questions)

    def save_questions(self, questions):
        try:
            self.QUESTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
            self.QUESTIONS_FILE.write_text(
                json.dumps({"questions": questions}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            self.questions = questions
            return True
        except OSError as error:
            self.show_save_error(error)
            return False

    def show_save_error(self, error):
        message = (
            "Unable to update the questions file. "
            f"Please check permissions and try again.\n\nDetails: {error}"
        )
        try:
            messagebox.showerror("Save error", message)
        except tk.TclError:
            print(f"Save error: {message}")

    def filter_questions(self, query):
        query = (query or "").strip().lower()
        self.filtered_questions = (
            [q for q in self.questions if query in q.get("title", "").lower()]
            if query
            else list(self.questions)
        )

    def add_question(self, title, definition, image_path):
        new_question = {"title": title, "definition": definition, "image": image_path}
        updated_questions = self.questions + [new_question]

        if self.save_questions(updated_questions):
            self.filtered_questions = list(self.questions)
            return new_question
        return None

    def update_question(self, old_question, title, definition, image_path):
        new_question = {"title": title, "definition": definition, "image": image_path}

        try:
            index = self.questions.index(old_question)
        except ValueError:
            index = None

        updated_questions = [q for q in self.questions if q is not old_question]
        insert_index = index if index is not None else len(updated_questions)
        updated_questions.insert(insert_index, new_question)

        return (
            self.questions[insert_index]
            if self.save_questions(updated_questions)
            else None
        )

    def delete_question(self, question):
        try:
            index = self.questions.index(question)
        except ValueError:
            return False

        updated_questions = self.questions[:index] + self.questions[index + 1 :]

        if self.save_questions(updated_questions):
            self.filtered_questions = [
                q for q in self.filtered_questions if q is not question
            ]
            return True
        return False

    def validate_title_unique(self, title, exclude_question=None):
        normalized = title.lower()
        return not any(
            q.get("title", "").strip().lower() == normalized
            for q in self.questions
            if q is not exclude_question
        )

    def build_ui(self):
        self.parent.grid_rowconfigure(0, weight=1)
        self.parent.grid_columnconfigure(0, weight=1)

        main = ctk.CTkFrame(self.parent, fg_color="transparent")
        main.grid(row=0, column=0, sticky="nsew")
        main.grid_rowconfigure(1, weight=1)
        for col, (weight, minsize) in enumerate([(0, 0), (0, 2), (1, 0)]):
            main.grid_columnconfigure(col, weight=weight, minsize=minsize)

        self.build_header(main)
        self.build_sidebar(main)
        self.build_divider(main)
        self.build_detail_panel(main)

    def build_header(self, parent):
        c = self.COLORS
        header = ctk.CTkFrame(parent, fg_color=c["header_bg"], corner_radius=0)
        header.grid(row=0, column=0, columnspan=3, sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            header,
            text="Menu",
            font=self.button_font,
            text_color=c["text_white"],
            image=self.back_arrow_icon,
            compound="left",
            anchor="w",
            fg_color="transparent",
            hover_color=c["header_hover"],
            command=self.return_to_menu,
            corner_radius=8,
            width=110,
            height=44,
        ).grid(row=0, column=0, padx=(24, 16), pady=(28, 32), sticky="w")

        ctk.CTkLabel(
            header,
            text="Manage Questions",
            font=self.title_font,
            text_color=c["text_white"],
            anchor="center",
        ).grid(row=0, column=1, padx=32, pady=(28, 32), sticky="nsew")

    def build_sidebar(self, parent):
        sidebar = ctk.CTkFrame(parent, fg_color="transparent")
        sidebar.grid(row=1, column=0, sticky="ns", padx=(32, 12), pady=32)
        sidebar.grid_rowconfigure(1, weight=1)
        sidebar.grid_columnconfigure(0, weight=1)

        self.build_controls(sidebar)
        self.build_question_list_container(sidebar)

    def build_controls(self, parent):
        c = self.COLORS
        controls = ctk.CTkFrame(parent, fg_color="transparent")
        controls.grid(row=0, column=0, sticky="ew")
        controls.grid_columnconfigure(0, weight=1)

        # Search bar
        search_wrapper = ctk.CTkFrame(
            controls, fg_color=c["search_bg"], corner_radius=18
        )
        search_wrapper.grid(row=0, column=0, padx=(16, 12), pady=16, sticky="ew")
        search_wrapper.grid_columnconfigure(1, weight=1)

        # Search icon
        icon_config = {
            "text": "",
            "image": self.search_icon,
            "fg_color": "transparent",
            "width": 32,
        }
        if not self.search_icon:
            icon_config.update(
                {"text": "S", "text_color": c["text_white"], "font": self.button_font}
            )

        ctk.CTkLabel(search_wrapper, **icon_config).grid(
            row=0, column=0, padx=(18, 8), sticky="w"
        )

        # Search entry
        self.search_entry = ctk.CTkEntry(
            search_wrapper,
            placeholder_text="Search...",
            placeholder_text_color=c["text_placeholder"],
            fg_color="transparent",
            text_color=c["text_white"],
            font=self.search_font,
            corner_radius=0,
            height=42,
            border_width=0,
        )
        self.search_entry.grid(row=0, column=1, padx=(0, 18), pady=4, sticky="nsew")
        for event in ("<KeyRelease>", "<<Paste>>", "<<Cut>>"):
            self.search_entry.bind(event, lambda e: self.handle_search())

        # Add button
        ctk.CTkButton(
            controls,
            text="Add",
            font=self.button_font,
            fg_color=c["primary"],
            hover_color=c["primary_hover"],
            command=self.on_add_clicked,
            width=96,
            height=42,
            corner_radius=12,
        ).grid(row=0, column=1, padx=(0, 16), pady=16)

    def build_question_list_container(self, parent):
        self.list_container = ctk.CTkFrame(parent, fg_color="transparent")
        self.list_container.grid(row=1, column=0, sticky="nsew", pady=(20, 0))
        self.list_container.grid_columnconfigure(0, weight=1)
        self.list_container.grid_rowconfigure(0, weight=1)

        self.render_question_list()

    def build_divider(self, parent):
        ctk.CTkFrame(
            parent,
            fg_color=self.COLORS["border_light"],
            corner_radius=0,
            width=2,
        ).grid(row=1, column=1, sticky="ns", pady=32)

    def build_detail_panel(self, parent):
        c = self.COLORS
        self.detail_container = ctk.CTkFrame(
            parent,
            fg_color=c["bg_light"],
            corner_radius=16,
            border_width=1,
            border_color=c["border_light"],
        )
        self.detail_container.grid(
            row=1, column=2, sticky="nsew", padx=(12, 32), pady=32
        )
        self.detail_container.grid_rowconfigure(1, weight=1)
        self.detail_container.grid_columnconfigure(0, weight=1)

        self.build_detail_header()
        self.build_detail_body()

        # Hide initially
        self.detail_container.grid_remove()
        self.detail_visible = False

    def build_detail_header(self):
        c = self.COLORS
        header = ctk.CTkFrame(self.detail_container, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(24, 12))
        header.grid_columnconfigure(0, weight=1)

        self.detail_title_label = ctk.CTkLabel(
            header,
            text="",
            font=self.detail_title_font,
            text_color=c["text_dark"],
            anchor="w",
        )
        self.detail_title_label.grid(row=0, column=0, sticky="w", padx=(12, 0))

        # Action buttons
        for col, (text, fg, hover, cmd) in enumerate(
            [
                ("Edit", c["secondary"], c["secondary_hover"], self.on_edit_clicked),
                ("Delete", c["danger"], c["danger_hover"], self.on_delete_clicked),
            ],
            start=1,
        ):
            ctk.CTkButton(
                header,
                text=text,
                font=self.question_font,
                fg_color=fg,
                hover_color=hover,
                command=cmd,
                width=110,
                height=44,
                corner_radius=12,
            ).grid(row=0, column=col, padx=(12, 12 if col == 1 else 0), sticky="e")

    def build_detail_body(self):
        c = self.COLORS
        body = ctk.CTkFrame(self.detail_container, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 24))
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=1)

        content = ctk.CTkFrame(body, fg_color="transparent")
        content.grid(row=0, column=0, sticky="n")
        content.grid_columnconfigure(0, weight=1)

        # Image label
        self.detail_image_label = ctk.CTkLabel(
            content,
            text="Image placeholder",
            font=self.search_font,
            text_color=c["text_light"],
            fg_color="transparent",
            width=220,
            height=220,
            anchor="center",
        )
        self.detail_image_label.grid(
            row=0, column=0, pady=(28, 48), padx=12, sticky="n"
        )

        try:
            self.detail_image_label.configure(image=self.detail_image_placeholder)
        except tk.TclError:
            pass

        # Definition row with audio button
        definition_row = ctk.CTkFrame(content, fg_color="transparent")
        definition_row.grid(row=1, column=0, sticky="ew", padx=32, pady=(32, 0))
        definition_row.grid_columnconfigure(1, weight=1)

        audio_config = {
            "text": "" if self.audio_icon else "Audio",
            "image": self.audio_icon,
            "fg_color": "transparent",
            "hover_color": "#E5E7EB",
            "command": self.on_audio_clicked,
            "state": "disabled",
            "width": 44,
            "height": 44,
            "corner_radius": 22,
        }
        if not self.audio_icon:
            audio_config.update(
                {"font": self.body_font, "text_color": c["text_medium"]}
            )

        self.definition_audio_button = ctk.CTkButton(definition_row, **audio_config)
        self.definition_audio_button.grid(row=0, column=0, sticky="nw", padx=(0, 16))

        self.detail_definition_label = ctk.CTkLabel(
            definition_row,
            text="",
            font=self.body_font,
            text_color=c["text_medium"],
            justify="left",
            anchor="w",
            wraplength=540,
        )
        self.detail_definition_label.grid(row=0, column=1, sticky="nw")

    def render_question_list(self):
        if not self.list_container or not self.list_container.winfo_exists():
            return

        # Clear existing widgets
        for child in self.list_container.winfo_children():
            child.destroy()

        c, s = self.COLORS, self.SIZES
        questions = self.filtered_questions

        # Check if selected question is visible
        selected_visible = (
            self.current_question in questions if self.current_question else False
        )
        if not selected_visible and self.current_question:
            self.clear_detail_panel()

        # Create frame with or without scrollbar
        frame_config = {
            "fg_color": c["bg_light"],
            "border_width": 1,
            "border_color": c["border_light"],
            "corner_radius": 24,
        }
        FrameClass = (
            ctk.CTkScrollableFrame
            if len(questions) > s["max_questions"]
            else ctk.CTkFrame
        )
        list_frame = FrameClass(self.list_container, **frame_config)
        list_frame.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        list_frame.grid_columnconfigure(0, weight=1)

        if not questions:
            # Show empty state
            search_query = self.search_entry.get() if self.search_entry else ""
            empty_text = (
                "No questions match your search."
                if search_query.strip()
                else "No questions available."
            )
            ctk.CTkLabel(
                list_frame,
                text=empty_text,
                font=self.body_font,
                text_color=c["text_lighter"],
            ).grid(row=1, column=0, padx=24, pady=(12, 24))
            return

        # Render question buttons
        self.selected_question_button = None
        for index, question in enumerate(questions, start=0):
            is_selected = selected_visible and question is self.current_question

            # Create button without command first
            button = ctk.CTkButton(
                list_frame,
                text=question.get("title", ""),
                font=self.question_font,
                text_color=c["text_white"] if is_selected else c["question_text"],
                fg_color=c["question_selected"] if is_selected else c["question_bg"],
                hover_color=(
                    c["question_selected"] if is_selected else c["question_hover"]
                ),
                border_width=0,
                height=s["question_btn_height"],
                corner_radius=s["question_corner_radius"],
            )

            # Configure command after button is created to properly capture reference
            button.configure(
                command=lambda q=question, b=button: self.on_question_selected(q, b)
            )

            button.grid(
                row=index,
                column=0,
                sticky="nsew",
                padx=s["question_margin"],
                pady=s["question_padding"],
            )

            if is_selected:
                self.selected_question_button = button

    def handle_search(self):
        query = self.search_entry.get() if self.search_entry else ""
        self.filter_questions(query)
        self.render_question_list()

    def on_question_selected(self, question, button):
        self.tts.stop()

        # Show detail panel if hidden
        if not self.detail_visible:
            self.detail_container.grid()
            self.detail_visible = True

        c = self.COLORS
        # Update button selection
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

        # Update detail content
        self.current_question = question
        title = question.get("title", "")
        definition = (
            question.get("definition", "").strip() or "No definition available yet."
        )
        image_path = question.get("image", "")

        self.detail_title_label.configure(text=title)
        self.detail_definition_label.configure(text=definition)

        # Update image
        detail_image = self.image_handler.create_detail_image(
            image_path, self.SIZES["detail_image"]
        )
        try:
            self.detail_image_label.configure(
                image=detail_image or self.detail_image_placeholder,
                text="" if detail_image else "Image not available",
            )
        except tk.TclError:
            pass

        # Enable/disable audio button
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

        # Reset widgets
        widgets = [
            (self.detail_title_label, {"text": ""}),
            (self.detail_definition_label, {"text": ""}),
            (self.definition_audio_button, {"state": "disabled"}),
        ]
        for widget, config in widgets:
            if widget and widget.winfo_exists():
                widget.configure(**config)

        if self.detail_image_label and self.detail_image_label.winfo_exists():
            try:
                self.detail_image_label.configure(
                    image=self.detail_image_placeholder, text="Image placeholder"
                )
            except tk.TclError:
                pass

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

    def on_add_clicked(self):
        ui_config = self.create_modal_ui_config(self.get_standard_modal_keys())
        AddQuestionModal(
            self.parent, ui_config, self.image_handler, self.handle_add_save
        ).show()

    def handle_add_save(self, title, definition, source_image_path):
        if not self.validate_title_unique(title):
            messagebox.showwarning(
                "Duplicate Question",
                "A question with this title already exists. Please use a different title.",
            )
            return

        # Copy image to project
        relative_image_path = self.image_handler.copy_image_to_project(
            source_image_path
        )
        if not relative_image_path:
            return  # Error already shown

        # Add question and update UI
        new_question = self.add_question(
            title, definition, relative_image_path.as_posix()
        )
        if new_question:
            self.current_question = new_question
            if self.search_entry:
                try:
                    self.search_entry.delete(0, tk.END)
                except tk.TclError:
                    pass
            self.render_question_list()
            # After render_question_list, selected_question_button is updated
            # Only call on_question_selected if button was found and set during render
            if self.selected_question_button:
                self.on_question_selected(new_question, self.selected_question_button)

    def on_edit_clicked(self):
        if not self.current_question:
            return
        self.tts.stop()
        ui_config = self.create_modal_ui_config(self.get_standard_modal_keys())
        EditQuestionModal(
            self.parent, ui_config, self.image_handler, self.handle_edit_save
        ).show(self.current_question)

    def handle_edit_save(self, title, definition, image_path):
        if not self.validate_title_unique(
            title, exclude_question=self.current_question
        ):
            messagebox.showwarning(
                "Duplicate Question",
                "A question with this title already exists. Please use a different title.",
            )
            return

        # Handle image path
        stored_image_path = image_path
        if hasattr(image_path, "as_posix"):
            relative_image_path = self.image_handler.copy_image_to_project(image_path)
            if not relative_image_path:
                return  # Error already shown
            stored_image_path = relative_image_path.as_posix()

        # Update question and UI
        updated_question = self.update_question(
            self.current_question, title, definition, stored_image_path
        )
        if updated_question:
            self.current_question = updated_question
            self.handle_search()
            # After handle_search, selected_question_button is updated during render
            # Only call on_question_selected if button was found and set during render
            if self.selected_question_button:
                self.on_question_selected(
                    updated_question, self.selected_question_button
                )

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
        DeleteConfirmationModal(
            self.parent, ui_config, self.handle_delete_confirm
        ).show()

    def handle_delete_confirm(self):
        if self.current_question and self.delete_question(self.current_question):
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

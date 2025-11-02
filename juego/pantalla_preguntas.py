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
    QUESTIONS_FILE = Path(__file__).resolve().parent.parent / "datos" / "preguntas.json"
    IMAGES_DIR = Path(__file__).resolve().parent.parent / "recursos" / "imagenes"
    AUDIO_DIR = Path(__file__).resolve().parent.parent / "recursos" / "audio"

    # Icon filenames
    AUDIO_ICON_FILENAME = "volume.svg"
    SEARCH_ICON_FILENAME = "search.svg"
    BACK_ARROW_FILENAME = "arrow.svg"

    # UI Colors
    HEADER_BG = "#1C2534"
    HEADER_HOVER = "#273246"
    PRIMARY_BLUE = "#1D6CFF"
    PRIMARY_BLUE_HOVER = "#0F55C9"
    SECONDARY_CYAN = "#00CFC5"
    SECONDARY_CYAN_HOVER = "#04AFA6"
    DANGER_RED = "#FF4F60"
    DANGER_RED_HOVER = "#E53949"
    SUCCESS_GREEN = "#047857"
    BG_LIGHT = "#F5F7FA"
    BG_WHITE = "#FFFFFF"
    BORDER_LIGHT = "#D2DAE6"
    BORDER_MEDIUM = "#CBD5E1"
    SEARCH_BG = "#D1D8E0"
    TEXT_DARK = "#111827"
    TEXT_MEDIUM = "#1F2937"
    TEXT_LIGHT = "#4B5563"
    TEXT_LIGHTER = "#6B7280"
    TEXT_WHITE = "#FFFFFF"
    TEXT_PLACEHOLDER = "#F5F7FA"
    TEXT_ERROR = "#DC2626"
    BUTTON_CANCEL_BG = "#E5E7EB"
    BUTTON_CANCEL_HOVER = "#CBD5E1"
    QUESTION_DEFAULT_BG = "transparent"
    QUESTION_DEFAULT_TEXT = "#1F2937"
    QUESTION_DEFAULT_HOVER = "#E2E8F0"
    QUESTION_SELECTED_BG = "#1D6CFF"

    # UI Sizes
    MAX_VISIBLE_QUESTIONS = 8
    DETAIL_IMAGE_MAX_SIZE = (220, 220)
    AUDIO_ICON_SIZE = (32, 32)
    SEARCH_ICON_SIZE = (16, 16)
    BACK_ARROW_SIZE = (20, 20)
    QUESTION_BUTTON_HEIGHT = 50
    QUESTION_BUTTON_SIDE_MARGIN = 1
    QUESTION_BUTTON_VERTICAL_PADDING = 1

    def __init__(self, parent, on_return_callback=None):
        self.parent = parent
        self.on_return_callback = on_return_callback

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

        # Cached images
        self.detail_image_placeholder = (
            self.image_handler.create_transparent_placeholder()
        )
        self.audio_icon = self.image_handler.create_ctk_icon(
            self.AUDIO_ICON_FILENAME, self.AUDIO_ICON_SIZE
        )
        self.search_icon = self.image_handler.create_ctk_icon(
            self.SEARCH_ICON_FILENAME, self.SEARCH_ICON_SIZE
        )
        self.back_arrow_icon = self.image_handler.create_ctk_icon(
            self.BACK_ARROW_FILENAME, self.BACK_ARROW_SIZE
        )

        # Clear parent and build UI
        for widget in self.parent.winfo_children():
            widget.destroy()

        self.build_ui()

    def init_fonts(self):
        self.title_font = ctk.CTkFont(
            family="Poppins ExtraBold", size=38, weight="bold"
        )
        self.body_font = ctk.CTkFont(family="Poppins Medium", size=18)
        self.button_font = ctk.CTkFont(
            family="Poppins SemiBold", size=16, weight="bold"
        )
        self.cancel_button_font = ctk.CTkFont(
            family="Poppins ExtraBold", size=16, weight="bold"
        )
        self.search_font = ctk.CTkFont(
            family="Poppins SemiBold", size=18, weight="bold"
        )
        self.question_font = ctk.CTkFont(
            family="Poppins SemiBold", size=18, weight="bold"
        )
        self.detail_title_font = ctk.CTkFont(
            family="Poppins ExtraBold", size=38, weight="bold"
        )
        self.dialog_title_font = ctk.CTkFont(
            family="Poppins SemiBold", size=24, weight="bold"
        )
        self.dialog_body_font = ctk.CTkFont(family="Poppins Medium", size=16)
        self.dialog_label_font = ctk.CTkFont(
            family="Poppins SemiBold", size=16, weight="bold"
        )

    def load_questions(self):
        if not self.QUESTIONS_FILE.exists():
            self.questions = []
            self.filtered_questions = []
            return

        try:
            data = json.loads(self.QUESTIONS_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            self.questions = []
            self.filtered_questions = []
            return

        raw_questions = data.get("questions", []) if isinstance(data, dict) else data

        questions = []
        for item in raw_questions:
            if not isinstance(item, dict):
                continue

            title = (item.get("title") or "").strip()
            if not title:
                continue

            definition = (item.get("definition") or "").strip()
            image = (item.get("image") or "").strip()
            questions.append(
                {
                    "title": title,
                    "definition": definition,
                    "image": image,
                }
            )

        self.questions = questions
        self.filtered_questions = list(questions)

    def save_questions(self, questions):
        payload = {"questions": questions}

        try:
            self.QUESTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
            self.QUESTIONS_FILE.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as error:
            self.show_save_error(error)
            return False

        self.questions = questions
        return True

    def show_save_error(self, error):
        base_message = (
            "Unable to update the questions file. "
            "Please check permissions and try again."
        )
        detail = f"\n\nDetails: {error}" if error else ""
        message = f"{base_message}{detail}"

        try:
            messagebox.showerror("Save error", message)
        except tk.TclError:
            print(f"Save error: {message}")

    def filter_questions(self, query):
        query = (query or "").strip().lower()

        if query:
            self.filtered_questions = [
                question
                for question in self.questions
                if query in (question.get("title") or "").lower()
            ]
        else:
            self.filtered_questions = list(self.questions)

    def add_question(self, title, definition, image_path):
        new_question = {
            "title": title,
            "definition": definition,
            "image": image_path,
        }

        updated_questions = list(self.questions)
        updated_questions.append(new_question)

        if not self.save_questions(updated_questions):
            return None

        self.filtered_questions = list(self.questions)
        return new_question

    def update_question(self, old_question, title, definition, image_path):
        new_question = {
            "title": title,
            "definition": definition,
            "image": image_path,
        }

        try:
            current_index = self.questions.index(old_question)
        except ValueError:
            current_index = None

        updated_questions = [
            question for question in self.questions if question is not old_question
        ]

        insert_index = (
            current_index if current_index is not None else len(updated_questions)
        )
        updated_questions.insert(insert_index, new_question)

        if not self.save_questions(updated_questions):
            return None

        return self.questions[insert_index]

    def delete_question(self, question):
        target_index = None
        for index, candidate in enumerate(self.questions):
            if candidate is question:
                target_index = index
                break

        if target_index is None:
            return False

        updated_questions = list(self.questions)
        updated_questions.pop(target_index)

        if not self.save_questions(updated_questions):
            return False

        self.filtered_questions = [
            q for q in self.filtered_questions if q is not question
        ]
        return True

    def validate_title_unique(self, title, exclude_question=None):
        normalized_title = title.lower()
        for existing in self.questions:
            if existing is exclude_question:
                continue

            existing_title = (existing.get("title") or "").strip().lower()
            if existing_title == normalized_title:
                return False

        return True

    def build_ui(self):
        self.parent.grid_rowconfigure(0, weight=1)
        self.parent.grid_columnconfigure(0, weight=1)

        main = ctk.CTkFrame(self.parent, fg_color="transparent")
        main.grid(row=0, column=0, sticky="nsew")
        main.grid_rowconfigure(1, weight=1)
        main.grid_columnconfigure(0, weight=0)
        main.grid_columnconfigure(1, weight=0, minsize=2)
        main.grid_columnconfigure(2, weight=1)

        self.build_header(main)
        self.build_sidebar(main)
        self.build_divider(main)
        self.build_detail_panel(main)

    def build_header(self, parent):
        header = ctk.CTkFrame(parent, fg_color=self.HEADER_BG, corner_radius=0)
        header.grid(row=0, column=0, columnspan=3, sticky="ew")
        header.grid_columnconfigure(0, weight=0)
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            header,
            text="Menu",
            font=self.button_font,
            text_color=self.TEXT_WHITE,
            image=self.back_arrow_icon,
            compound="left",
            anchor="w",
            fg_color="transparent",
            hover_color=self.HEADER_HOVER,
            command=self.return_to_menu,
            corner_radius=8,
            width=110,
            height=44,
        ).grid(row=0, column=0, padx=(24, 16), pady=(28, 32), sticky="w")

        ctk.CTkLabel(
            header,
            text="Manage Questions",
            font=self.title_font,
            text_color=self.TEXT_WHITE,
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
        controls = ctk.CTkFrame(parent, fg_color="transparent")
        controls.grid(row=0, column=0, sticky="ew")
        controls.grid_columnconfigure(0, weight=1)

        # Search bar
        search_wrapper = ctk.CTkFrame(
            controls, fg_color=self.SEARCH_BG, corner_radius=18
        )
        search_wrapper.grid(row=0, column=0, padx=(16, 12), pady=16, sticky="ew")
        search_wrapper.grid_columnconfigure(1, weight=1)

        # Search icon
        icon_kwargs = {
            "text": "",
            "image": self.search_icon,
            "fg_color": "transparent",
            "width": 32,
        }
        if not self.search_icon:
            icon_kwargs.update(
                {"text": "S", "text_color": self.TEXT_WHITE, "font": self.button_font}
            )

        ctk.CTkLabel(search_wrapper, **icon_kwargs).grid(
            row=0, column=0, padx=(18, 8), sticky="w"
        )

        # Search entry
        self.search_entry = ctk.CTkEntry(
            search_wrapper,
            placeholder_text="Search...",
            placeholder_text_color=self.TEXT_PLACEHOLDER,
            fg_color="transparent",
            text_color=self.TEXT_WHITE,
            font=self.search_font,
            corner_radius=0,
            height=42,
            border_width=0,
        )
        self.search_entry.grid(row=0, column=1, padx=(0, 18), pady=4, sticky="nsew")
        self.search_entry.bind("<KeyRelease>", lambda e: self.handle_search())
        self.search_entry.bind("<<Paste>>", lambda e: self.handle_search())
        self.search_entry.bind("<<Cut>>", lambda e: self.handle_search())

        # Add button
        ctk.CTkButton(
            controls,
            text="Add",
            font=self.button_font,
            fg_color=self.PRIMARY_BLUE,
            hover_color=self.PRIMARY_BLUE_HOVER,
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
            fg_color=self.BORDER_LIGHT,
            corner_radius=0,
            width=2,
        ).grid(row=1, column=1, sticky="ns", pady=32)

    def build_detail_panel(self, parent):
        self.detail_container = ctk.CTkFrame(
            parent,
            fg_color=self.BG_LIGHT,
            corner_radius=16,
            border_width=1,
            border_color=self.BORDER_LIGHT,
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
        header = ctk.CTkFrame(self.detail_container, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(24, 12))
        header.grid_columnconfigure(0, weight=1)

        self.detail_title_label = ctk.CTkLabel(
            header,
            text="",
            font=self.detail_title_font,
            text_color=self.TEXT_DARK,
            anchor="w",
        )
        self.detail_title_label.grid(row=0, column=0, sticky="w", padx=(12, 0))

        ctk.CTkButton(
            header,
            text="Edit",
            font=self.question_font,
            fg_color=self.SECONDARY_CYAN,
            hover_color=self.SECONDARY_CYAN_HOVER,
            command=self.on_edit_clicked,
            width=110,
            height=44,
            corner_radius=12,
        ).grid(row=0, column=1, padx=(12, 12), sticky="e")

        ctk.CTkButton(
            header,
            text="Delete",
            font=self.question_font,
            fg_color=self.DANGER_RED,
            hover_color=self.DANGER_RED_HOVER,
            command=self.on_delete_clicked,
            width=110,
            height=44,
            corner_radius=12,
        ).grid(row=0, column=2, sticky="e")

    def build_detail_body(self):
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
            text_color=self.TEXT_LIGHT,
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

        audio_kwargs = {
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
            audio_kwargs.update(
                {"font": self.body_font, "text_color": self.TEXT_MEDIUM}
            )

        self.definition_audio_button = ctk.CTkButton(definition_row, **audio_kwargs)
        self.definition_audio_button.grid(row=0, column=0, sticky="nw", padx=(0, 16))

        self.detail_definition_label = ctk.CTkLabel(
            definition_row,
            text="",
            font=self.body_font,
            text_color=self.TEXT_MEDIUM,
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

        questions = self.filtered_questions

        # Check if selected question is visible
        selected_visible = (
            self.current_question in questions if self.current_question else False
        )
        if not selected_visible and self.current_question:
            self.clear_detail_panel()

        # Determine if scrollbar is needed
        needs_scrollbar = len(questions) > self.MAX_VISIBLE_QUESTIONS

        # Create frame
        frame_kwargs = {
            "fg_color": self.BG_LIGHT,
            "border_width": 1,
            "border_color": self.BORDER_LIGHT,
            "corner_radius": 24,
        }

        if needs_scrollbar:
            list_frame = ctk.CTkScrollableFrame(self.list_container, **frame_kwargs)
        else:
            list_frame = ctk.CTkFrame(self.list_container, **frame_kwargs)

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
                text_color=self.TEXT_LIGHTER,
            ).grid(row=1, column=0, padx=24, pady=(12, 24))
            return

        # Render question buttons
        self.selected_question_button = None
        for index, question in enumerate(questions, start=1):
            button = ctk.CTkButton(
                list_frame,
                text=question.get("title", ""),
                font=self.question_font,
                text_color=self.QUESTION_DEFAULT_TEXT,
                fg_color=self.QUESTION_DEFAULT_BG,
                hover_color=self.QUESTION_DEFAULT_HOVER,
                border_width=0,
                height=self.QUESTION_BUTTON_HEIGHT,
            )
            # Update command to pass button reference
            button.configure(
                command=lambda q=question, b=button: self.on_question_selected(q, b)
            )

            button.grid(
                row=index,
                column=0,
                sticky="nsew",
                padx=self.QUESTION_BUTTON_SIDE_MARGIN,
                pady=(
                    0 if index == 1 else self.QUESTION_BUTTON_VERTICAL_PADDING,
                    self.QUESTION_BUTTON_VERTICAL_PADDING,
                ),
            )

            # Highlight if selected
            if selected_visible and question is self.current_question:
                button.configure(
                    fg_color=self.QUESTION_SELECTED_BG,
                    text_color=self.TEXT_WHITE,
                    hover_color=self.QUESTION_SELECTED_BG,
                )
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

        # Update button selection
        if (
            self.selected_question_button
            and self.selected_question_button is not button
        ):
            self.selected_question_button.configure(
                fg_color=self.QUESTION_DEFAULT_BG,
                text_color=self.QUESTION_DEFAULT_TEXT,
                hover_color=self.QUESTION_DEFAULT_HOVER,
            )

        button.configure(
            fg_color=self.QUESTION_SELECTED_BG,
            text_color=self.TEXT_WHITE,
            hover_color=self.QUESTION_SELECTED_BG,
        )
        self.selected_question_button = button

        # Update detail content
        self.current_question = question
        title = question.get("title", "")
        definition = (
            question.get("definition") or ""
        ).strip() or "No definition available yet."
        image_path = question.get("image", "")

        self.detail_title_label.configure(text=title)
        self.detail_definition_label.configure(text=definition)

        # Update image
        detail_image = self.image_handler.create_detail_image(
            image_path, self.DETAIL_IMAGE_MAX_SIZE
        )

        try:
            if detail_image:
                self.detail_image_label.configure(image=detail_image, text="")
            else:
                self.detail_image_label.configure(
                    image=self.detail_image_placeholder, text="Image not available"
                )
        except tk.TclError:
            pass

        # Enable/disable audio button
        has_definition = bool((question.get("definition") or "").strip())
        self.definition_audio_button.configure(
            state="normal" if has_definition else "disabled"
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

        if self.detail_title_label and self.detail_title_label.winfo_exists():
            self.detail_title_label.configure(text="")

        if self.detail_definition_label and self.detail_definition_label.winfo_exists():
            self.detail_definition_label.configure(text="")

        if self.definition_audio_button and self.definition_audio_button.winfo_exists():
            self.definition_audio_button.configure(state="disabled")

        if self.detail_image_label and self.detail_image_label.winfo_exists():
            try:
                self.detail_image_label.configure(
                    image=self.detail_image_placeholder, text="Image placeholder"
                )
            except tk.TclError:
                pass

    def on_add_clicked(self):
        # Create UI config object for modal
        ui_config = type(
            "UIConfig",
            (),
            {
                "BG_LIGHT": self.BG_LIGHT,
                "BG_WHITE": self.BG_WHITE,
                "BG_MODAL_HEADER": "#202632",
                "BORDER_MEDIUM": self.BORDER_MEDIUM,
                "PRIMARY_BLUE": self.PRIMARY_BLUE,
                "PRIMARY_BLUE_HOVER": self.PRIMARY_BLUE_HOVER,
                "BUTTON_CANCEL_BG": self.BUTTON_CANCEL_BG,
                "BUTTON_CANCEL_HOVER": self.BUTTON_CANCEL_HOVER,
                "TEXT_DARK": self.TEXT_DARK,
                "TEXT_WHITE": self.TEXT_WHITE,
                "TEXT_LIGHT": self.TEXT_LIGHT,
                "TEXT_ERROR": self.TEXT_ERROR,
                "SUCCESS_GREEN": self.SUCCESS_GREEN,
                "dialog_title_font": self.dialog_title_font,
                "dialog_label_font": self.dialog_label_font,
                "body_font": self.body_font,
                "button_font": self.button_font,
                "cancel_button_font": self.cancel_button_font,
            },
        )()

        modal = AddQuestionModal(
            self.parent, ui_config, self.image_handler, self.handle_add_save
        )
        modal.show()

    def handle_add_save(self, title, definition, source_image_path):
        # Validate title uniqueness
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
            return  # Error already shown by image_handler

        stored_image_path = relative_image_path.as_posix()

        # Add question
        new_question = self.add_question(title, definition, stored_image_path)
        if not new_question:
            return  # Error already shown

        # Update UI
        self.current_question = new_question
        if self.search_entry:
            try:
                self.search_entry.delete(0, tk.END)
            except tk.TclError:
                pass

        self.render_question_list()

        if self.selected_question_button:
            self.on_question_selected(new_question, self.selected_question_button)

    def on_edit_clicked(self):
        if not self.current_question:
            return

        self.tts.stop()

        # Create UI config object for modal
        ui_config = type(
            "UIConfig",
            (),
            {
                "BG_LIGHT": self.BG_LIGHT,
                "BG_WHITE": self.BG_WHITE,
                "BG_MODAL_HEADER": "#202632",
                "BORDER_MEDIUM": self.BORDER_MEDIUM,
                "PRIMARY_BLUE": self.PRIMARY_BLUE,
                "PRIMARY_BLUE_HOVER": self.PRIMARY_BLUE_HOVER,
                "BUTTON_CANCEL_BG": self.BUTTON_CANCEL_BG,
                "BUTTON_CANCEL_HOVER": self.BUTTON_CANCEL_HOVER,
                "TEXT_DARK": self.TEXT_DARK,
                "TEXT_WHITE": self.TEXT_WHITE,
                "TEXT_LIGHT": self.TEXT_LIGHT,
                "TEXT_ERROR": self.TEXT_ERROR,
                "SUCCESS_GREEN": self.SUCCESS_GREEN,
                "dialog_title_font": self.dialog_title_font,
                "dialog_label_font": self.dialog_label_font,
                "body_font": self.body_font,
                "button_font": self.button_font,
                "cancel_button_font": self.cancel_button_font,
            },
        )()

        modal = EditQuestionModal(
            self.parent, ui_config, self.image_handler, self.handle_edit_save
        )
        modal.show(self.current_question)

    def handle_edit_save(self, title, definition, image_path):
        # Validate title uniqueness
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
        if isinstance(image_path, Path):
            # New image selected
            relative_image_path = self.image_handler.copy_image_to_project(image_path)
            if not relative_image_path:
                return  # Error already shown
            stored_image_path = relative_image_path.as_posix()

        # Update question
        updated_question = self.update_question(
            self.current_question, title, definition, stored_image_path
        )
        if not updated_question:
            return  # Error already shown

        # Update UI
        self.current_question = updated_question
        self.handle_search()

        if self.selected_question_button:
            self.on_question_selected(updated_question, self.selected_question_button)

    def on_delete_clicked(self):
        if not self.current_question:
            return

        self.tts.stop()

        # Create UI config object for modal
        ui_config = type(
            "UIConfig",
            (),
            {
                "BG_LIGHT": self.BG_LIGHT,
                "BG_MODAL_HEADER": "#202632",
                "DANGER_RED": self.DANGER_RED,
                "DANGER_RED_HOVER": self.DANGER_RED_HOVER,
                "BUTTON_CANCEL_BG": self.BUTTON_CANCEL_BG,
                "BUTTON_CANCEL_HOVER": self.BUTTON_CANCEL_HOVER,
                "TEXT_DARK": self.TEXT_DARK,
                "TEXT_WHITE": self.TEXT_WHITE,
                "dialog_title_font": self.dialog_title_font,
                "dialog_body_font": self.dialog_body_font,
                "button_font": self.button_font,
                "cancel_button_font": self.cancel_button_font,
            },
        )()

        modal = DeleteConfirmationModal(
            self.parent, ui_config, self.handle_delete_confirm
        )
        modal.show()

    def handle_delete_confirm(self):
        if not self.current_question:
            return

        if not self.delete_question(self.current_question):
            return  # Error already shown

        # Update UI
        self.clear_detail_panel()
        self.handle_search()

    def on_audio_clicked(self):
        if not self.current_question:
            return

        definition = (self.current_question.get("definition") or "").strip()
        if definition:
            self.tts.speak(definition)

    def return_to_menu(self):
        self.tts.stop()
        if self.on_return_callback:
            self.on_return_callback()

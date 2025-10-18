import json
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path

import customtkinter as ctk
from PIL import Image, ImageTk
from tksvg import SvgImage as TkSvgImage

from juego.tts_service import TTSService


class ManageQuestionsScreen:
    HEADER_TEXT = "Manage Questions"
    MAX_VISIBLE_QUESTIONS = 8
    QUESTIONS_FILE = Path(__file__).resolve().parent.parent / "datos" / "preguntas.json"
    IMAGES_DIR = Path(__file__).resolve().parent.parent / "recursos" / "imagenes"
    DETAIL_IMAGE_MAX_SIZE = (220, 220)
    AUDIO_ICON_FILENAME = "volume.svg"
    AUDIO_ICON_SIZE = (32, 32)
    SEARCH_ICON_FILENAME = "search.svg"
    SEARCH_ICON_SIZE = (16, 16)
    SVG_RASTER_SCALE = 2.0
    QUESTION_DEFAULT_BG = "transparent"
    QUESTION_DEFAULT_TEXT = "#1F2937"
    QUESTION_DEFAULT_HOVER = "#E2E8F0"
    QUESTION_SELECTED_BG = "#1D6CFF"
    QUESTION_BUTTON_SIDE_MARGIN = 1
    QUESTION_BUTTON_HEIGHT = 50
    QUESTION_BUTTON_VERTICAL_PADDING = 1
    AUDIO_DIR = Path(__file__).resolve().parent.parent / "recursos" / "audio"

    def __init__(self, parent, on_return_callback=None):
        self.parent = parent
        self.on_return_callback = on_return_callback
        self.detail_visible = False
        self.selected_question_button = None
        self.question_selected_text_color = "#FFFFFF"
        self.questions = self.load_questions()
        self.filtered_questions = list(self.questions)
        self.current_image_path = ""
        self.add_button: None
        self.detail_container: None
        self.detail_title_label: None
        self.edit_button: None
        self.delete_button: None
        self.delete_modal = None
        self.add_modal = None
        self.add_concept_entry = None
        self.add_definition_textbox = None
        self.add_image_display_label = None
        self.add_image_feedback_label = None
        self.add_selected_image_source_path = None
        self.detail_image_label: None
        self.detail_definition_label: None
        self.definition_audio_button: None
        self.definition_audio_image = None
        self.detail_image = None
        self.current_question = None
        self.search_entry = None
        self.search_icon_image = None
        self.list_container = None
        self.list_frame = None

        # Initialize TTS service
        self.tts = TTSService(self.AUDIO_DIR)

        for widget in self.parent.winfo_children():
            widget.destroy()

        self.title_font = ctk.CTkFont(
            family="Poppins ExtraBold",
            size=38,
            weight="bold",
        )
        self.body_font = ctk.CTkFont(family="Poppins Medium", size=18)
        self.button_font = ctk.CTkFont(
            family="Poppins SemiBold", size=16, weight="bold"
        )
        self.cancel_button_font = ctk.CTkFont(
            family="Poppins ExtraBold",
            size=16,
            weight="bold",
        )
        self.search_font = ctk.CTkFont(
            family="Poppins SemiBold", size=18, weight="bold"
        )
        self.question_font = ctk.CTkFont(
            family="Poppins SemiBold",
            size=18,
            weight="bold",
        )
        self.detail_title_font = ctk.CTkFont(
            family="Poppins ExtraBold",
            size=38,
            weight="bold",
        )
        self.dialog_title_font = ctk.CTkFont(
            family="Poppins SemiBold",
            size=24,
            weight="bold",
        )
        self.dialog_body_font = ctk.CTkFont(
            family="Poppins Medium",
            size=16,
        )
        self.dialog_label_font = ctk.CTkFont(
            family="Poppins SemiBold",
            size=16,
            weight="bold",
        )

        self.build_ui()

    def load_questions(self):
        if not self.QUESTIONS_FILE.exists():
            return []

        try:
            data = json.loads(self.QUESTIONS_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []

        if isinstance(data, dict):
            raw_questions = data.get("questions", [])
        else:
            raw_questions = data

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

        return questions

    def save_questions(self, questions):
        payload = {"questions": questions}

        try:
            self.QUESTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
            self.QUESTIONS_FILE.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as error:
            self._show_save_error(error)
            return False

        return True

    def _show_save_error(self, error):
        base_message = "Unable to update the questions file. Please check permissions and try again."
        detail = f"\n\nDetails: {error}" if error else ""
        message = f"{base_message}{detail}"

        try:
            messagebox.showerror("Save error", message)
        except tk.TclError:
            print(f"Save error: {message}")

    def build_ui(self):
        self.parent.grid_rowconfigure(0, weight=1)
        self.parent.grid_columnconfigure(0, weight=1)

        self.main = ctk.CTkFrame(self.parent, fg_color="transparent")
        self.main.grid(row=0, column=0, sticky="nsew")
        self.main.grid_rowconfigure(1, weight=1)
        self.main.grid_columnconfigure(0, weight=0)
        self.main.grid_columnconfigure(1, weight=0, minsize=2)
        self.main.grid_columnconfigure(2, weight=1)

        self.build_header()
        self.build_content()

    def build_header(self):
        header = ctk.CTkFrame(
            self.main,
            fg_color="#1C2534",
            corner_radius=0,
        )
        header.grid(row=0, column=0, columnspan=3, sticky="ew")
        header.grid_columnconfigure(0, weight=0)
        header.grid_columnconfigure(1, weight=1)

        back_button = ctk.CTkButton(
            header,
            text="< Menu",
            font=self.button_font,
            text_color="#FFFFFF",
            fg_color="transparent",
            hover_color="#273246",
            command=self.return_to_menu,
            corner_radius=8,
            border_width=0,
            width=110,
            height=44,
        )
        back_button.grid(row=0, column=0, padx=(24, 16), pady=(28, 32), sticky="w")

        title = ctk.CTkLabel(
            header,
            text=self.HEADER_TEXT,
            font=self.title_font,
            text_color="#FFFFFF",
            anchor="center",
            justify="center",
        )
        title.grid(row=0, column=1, padx=32, pady=(28, 32), sticky="nsew")

    def build_content(self):
        sidebar = ctk.CTkFrame(self.main, fg_color="transparent")
        sidebar.grid(row=1, column=0, sticky="ns", padx=(32, 12), pady=32)
        sidebar.grid_rowconfigure(1, weight=1)
        sidebar.grid_columnconfigure(0, weight=1)

        self.build_controls(sidebar)
        self.build_question_list(sidebar)

        divider = ctk.CTkFrame(
            self.main,
            fg_color="#D2DAE6",
            corner_radius=0,
            width=2,
        )
        divider.grid(row=1, column=1, sticky="ns", pady=32)

        detail_container = ctk.CTkFrame(
            self.main,
            fg_color="#F5F7FA",
            corner_radius=16,
            border_width=1,
            border_color="#D2DAE6",
        )
        detail_container.grid(row=1, column=2, sticky="nsew", padx=(12, 32), pady=32)
        detail_container.grid_rowconfigure(0, weight=0)
        detail_container.grid_rowconfigure(1, weight=1)
        detail_container.grid_columnconfigure(0, weight=1)

        detail_header = ctk.CTkFrame(
            detail_container,
            fg_color="transparent",
        )
        detail_header.grid(row=0, column=0, sticky="ew", padx=24, pady=(24, 12))
        detail_header.grid_columnconfigure(0, weight=1)
        detail_header.grid_columnconfigure(1, weight=0)
        detail_header.grid_columnconfigure(2, weight=0)

        self.detail_title_label = ctk.CTkLabel(
            detail_header,
            text="",
            font=self.detail_title_font,
            text_color="#111827",
            anchor="w",
            justify="left",
        )
        self.detail_title_label.grid(row=0, column=0, sticky="w", padx=(12, 0))

        self.edit_button = ctk.CTkButton(
            detail_header,
            text="Edit",
            font=self.question_font,
            fg_color="#00CFC5",
            hover_color="#04AFA6",
            command=self.on_edit_pressed,
            width=110,
            height=44,
            corner_radius=12,
        )
        self.edit_button.grid(row=0, column=1, padx=(12, 12), sticky="e")

        self.delete_button = ctk.CTkButton(
            detail_header,
            text="Delete",
            font=self.question_font,
            fg_color="#FF4F60",
            hover_color="#E53949",
            command=self.on_delete_pressed,
            width=110,
            height=44,
            corner_radius=12,
        )
        self.delete_button.grid(row=0, column=2, sticky="e")

        detail_body = ctk.CTkFrame(
            detail_container,
            fg_color="transparent",
        )
        detail_body.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 24))
        detail_body.grid_rowconfigure(0, weight=1)
        detail_body.grid_columnconfigure(0, weight=1)

        detail_content = ctk.CTkFrame(
            detail_body,
            fg_color="transparent",
        )
        detail_content.grid(row=0, column=0, sticky="n")
        detail_content.grid_columnconfigure(0, weight=1)

        self.detail_image_label = ctk.CTkLabel(
            detail_content,
            text="Image placeholder",
            font=self.search_font,
            text_color="#4B5563",
            fg_color="transparent",
            width=220,
            height=220,
            corner_radius=0,
            anchor="center",
        )
        self.detail_image_label.grid(
            row=0, column=0, pady=(28, 48), padx=12, sticky="n"
        )

        definition_row = ctk.CTkFrame(
            detail_content,
            fg_color="transparent",
        )
        definition_row.grid(row=1, column=0, sticky="ew", padx=32, pady=(32, 0))
        definition_row.grid_columnconfigure(0, weight=0)
        definition_row.grid_columnconfigure(1, weight=1)

        # Try to load audio icon, fallback to text
        self.ensure_audio_icon()

        self.definition_audio_button = ctk.CTkButton(
            definition_row,
            text="" if self.definition_audio_image else "Audio",
            image=self.definition_audio_image if self.definition_audio_image else None,
            font=self.body_font if not self.definition_audio_image else None,
            text_color="#1F2937" if not self.definition_audio_image else None,
            fg_color="transparent",
            hover_color="#E5E7EB",
            border_width=0,
            width=44,
            height=44,
            corner_radius=22,
            command=self.on_definition_audio_pressed,
            state="disabled",
        )
        self.definition_audio_button.grid(row=0, column=0, sticky="nw", padx=(0, 16))

        self.detail_definition_label = ctk.CTkLabel(
            definition_row,
            text="",
            font=self.body_font,
            text_color="#1F2937",
            justify="left",
            anchor="w",
            wraplength=540,
        )
        self.detail_definition_label.grid(row=0, column=1, sticky="nw")

        self.detail_container = detail_container
        self.detail_container.grid_remove()
        self.detail_visible = False

    def build_controls(self, container):
        controls = ctk.CTkFrame(
            container,
            fg_color="transparent",
        )
        controls.grid(row=0, column=0, sticky="ew")
        controls.grid_columnconfigure(0, weight=1)
        controls.grid_columnconfigure(1, weight=0)

        search_wrapper = ctk.CTkFrame(
            controls,
            fg_color="#D1D8E0",
            corner_radius=18,
        )
        search_wrapper.grid(row=0, column=0, padx=(16, 12), pady=16, sticky="ew")
        search_wrapper.grid_columnconfigure(1, weight=1)
        search_wrapper.grid_rowconfigure(0, weight=1)

        self.ensure_search_icon()
        search_icon_kwargs = {
            "text": "",
            "image": self.search_icon_image if self.search_icon_image else None,
            "fg_color": "transparent",
            "width": 32,
        }
        if not self.search_icon_image:
            search_icon_kwargs["text"] = "S"
            search_icon_kwargs["text_color"] = "#FFFFFF"
            search_icon_kwargs["font"] = self.button_font

        search_icon_label = ctk.CTkLabel(
            search_wrapper,
            **search_icon_kwargs,
        )
        search_icon_label.grid(row=0, column=0, padx=(18, 8), pady=0, sticky="w")

        self.search_entry = ctk.CTkEntry(
            search_wrapper,
            placeholder_text="Search...",
            placeholder_text_color="#F5F7FA",
            fg_color="transparent",
            text_color="#FFFFFF",
            font=self.search_font,
            corner_radius=0,
            height=42,
            border_width=0,
        )
        self.search_entry.grid(row=0, column=1, padx=(0, 18), pady=4, sticky="nsew")
        self.search_entry.bind("<KeyRelease>", self._handle_search_input_change)
        self.search_entry.bind("<<Paste>>", self._handle_search_input_change)
        self.search_entry.bind("<<Cut>>", self._handle_search_input_change)

        add_button = ctk.CTkButton(
            controls,
            text="Add",
            font=self.button_font,
            fg_color="#1D6CFF",
            hover_color="#0F55C9",
            command=self.on_add_pressed,
            width=96,
            height=42,
            corner_radius=12,
        )
        add_button.grid(row=0, column=1, padx=(0, 16), pady=16)
        self.add_button = add_button
        resolved_text_color = add_button.cget("text_color")
        if resolved_text_color:
            self.question_selected_text_color = resolved_text_color

    def build_question_list(self, container):
        self.list_container = ctk.CTkFrame(
            container,
            fg_color="transparent",
        )
        self.list_container.grid(row=1, column=0, sticky="nsew", pady=(20, 0))
        self.list_container.grid_columnconfigure(0, weight=1)
        self.list_container.grid_rowconfigure(0, weight=1)

        self.render_question_list()

    def _handle_search_input_change(self, *_):
        self.on_search_change()

    def on_search_change(self):
        query_source = self.search_entry.get() if self.search_entry else ""
        query = (query_source or "").strip().lower()

        if query:
            self.filtered_questions = [
                question
                for question in self.questions
                if query in (question.get("title") or "").lower()
            ]
        else:
            self.filtered_questions = list(self.questions)

        self.render_question_list()

    def render_question_list(self):
        if not self.list_container or not self.list_container.winfo_exists():
            return

        for child in self.list_container.winfo_children():
            child.destroy()

        questions = self.filtered_questions or []
        selected_visible = False
        if self.current_question:
            selected_visible = any(
                candidate is self.current_question for candidate in questions
            )
        if not selected_visible and self.current_question:
            self.clear_question_details()

        needs_scrollbar = len(questions) > self.MAX_VISIBLE_QUESTIONS

        frame_kwargs = {
            "fg_color": "#F5F7FA",
            "border_width": 1,
            "border_color": "#D2DAE6",
            "corner_radius": 24,
        }

        if needs_scrollbar:
            list_frame = ctk.CTkScrollableFrame(
                self.list_container,
                **frame_kwargs,
            )
        else:
            list_frame = ctk.CTkFrame(
                self.list_container,
                **frame_kwargs,
            )

        list_frame.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        self.list_frame = list_frame

        if needs_scrollbar:
            for child in list_frame.winfo_children():
                if isinstance(child, ctk.CTkScrollbar):
                    child.grid_configure(padx=(0, 6), pady=(6, 6))
                    break

        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, minsize=24)

        if not questions:
            search_value = self.search_entry.get() if self.search_entry else ""
            has_query = bool((search_value or "").strip())
            empty_label = ctk.CTkLabel(
                list_frame,
                text=(
                    "No questions match your search."
                    if has_query
                    else "No questions available."
                ),
                font=self.body_font,
                text_color="#6B7280",
            )
            empty_label.grid(row=1, column=0, padx=24, pady=(12, 24), sticky="nsew")
            list_frame.grid_rowconfigure(1, weight=1)
            self.selected_question_button = None
            return

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
            button.configure(
                command=lambda q=question, b=button: self.show_question_details(q, b)
            )
            button.grid(
                row=index,
                column=0,
                sticky="nsew",
                padx=(
                    self.QUESTION_BUTTON_SIDE_MARGIN,
                    self.QUESTION_BUTTON_SIDE_MARGIN,
                ),
                pady=(
                    (0 if index == 1 else self.QUESTION_BUTTON_VERTICAL_PADDING),
                    self.QUESTION_BUTTON_VERTICAL_PADDING,
                ),
            )
            list_frame.grid_rowconfigure(index, weight=0)

            if selected_visible and question is self.current_question:
                self.apply_selected_button_style(button)
                self.selected_question_button = button
            else:
                self.apply_default_button_style(button)

        list_frame.grid_columnconfigure(0, weight=1)

    def apply_default_button_style(self, button):
        if not button or not button.winfo_exists():
            return

        button.configure(
            fg_color=self.QUESTION_DEFAULT_BG,
            text_color=self.QUESTION_DEFAULT_TEXT,
            hover_color=self.QUESTION_DEFAULT_HOVER,
        )

    def apply_selected_button_style(self, button):
        if not button or not button.winfo_exists():
            return

        button.configure(
            fg_color=self.QUESTION_SELECTED_BG,
            text_color=self.question_selected_text_color,
            hover_color=self.QUESTION_SELECTED_BG,
        )

    def clear_question_details(self):
        self.tts.stop()
        self.current_question = None
        self.current_image_path = ""
        self.selected_question_button = None
        self.detail_image = None

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
            self.detail_image_label.configure(image=None, text="Image placeholder")
            self.detail_image_label.image = None

    def on_add_pressed(self):
        self.show_add_question_modal()

    def on_edit_pressed(self):
        # Placeholder for future edit-question flow
        pass

    def on_delete_pressed(self):
        if not self.current_question:
            return

        self.tts.stop()
        self.show_delete_confirmation_modal()

    def show_add_question_modal(self):
        if self.parent and not self.parent.winfo_exists():
            return

        if self.add_modal and self.add_modal.winfo_exists():
            try:
                self.add_modal.lift()
                self.add_modal.focus_force()
            except tk.TclError:
                pass
            return

        root = self.parent.winfo_toplevel() if self.parent else None
        modal_parent = root if root else self.parent

        modal = ctk.CTkToplevel(modal_parent)
        modal.title("Add Question")
        if root:
            modal.transient(root)

        try:
            modal.grab_set()
        except tk.TclError:
            pass

        modal.resizable(False, False)
        modal.configure(fg_color="#F5F7FA")
        modal.grid_rowconfigure(0, weight=1)
        modal.grid_columnconfigure(0, weight=1)

        container = ctk.CTkFrame(
            modal,
            fg_color="#F5F7FA",
            corner_radius=0,
        )
        container.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(1, weight=1)

        header_frame = ctk.CTkFrame(
            container,
            fg_color="#202632",
            corner_radius=0,
            height=72,
        )
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 24), padx=0)
        header_frame.grid_propagate(False)
        header_frame.grid_columnconfigure(0, weight=1)

        header_label = ctk.CTkLabel(
            header_frame,
            text="Add Question",
            font=self.dialog_title_font,
            text_color="#FFFFFF",
            anchor="center",
            justify="center",
        )
        header_label.grid(row=0, column=0, sticky="nsew", padx=24, pady=(28, 12))

        form_frame = ctk.CTkFrame(
            container,
            fg_color="#F5F7FA",
        )
        form_frame.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 24))
        form_frame.grid_columnconfigure(0, weight=1)
        form_frame.grid_rowconfigure(3, weight=0)

        concept_label = ctk.CTkLabel(
            form_frame,
            text="Concept",
            font=self.dialog_label_font,
            text_color="#111827",
            anchor="w",
            justify="left",
        )
        concept_label.grid(row=0, column=0, sticky="w", pady=(0, 8))

        concept_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="Enter concept",
            fg_color="#FFFFFF",
            text_color="#111827",
            border_color="#CBD5E1",
            border_width=2,
            height=44,
            font=self.body_font,
            corner_radius=16,
        )
        concept_entry.grid(row=1, column=0, sticky="ew", pady=(0, 16))

        definition_label = ctk.CTkLabel(
            form_frame,
            text="Definition",
            font=self.dialog_label_font,
            text_color="#111827",
            anchor="w",
            justify="left",
        )
        definition_label.grid(row=2, column=0, sticky="w", pady=(0, 8))

        definition_textbox = ctk.CTkEntry(
            form_frame,
            fg_color="#FFFFFF",
            text_color="#111827",
            border_color="#CBD5E1",
            border_width=2,
            height=44,
            font=self.body_font,
            placeholder_text="Enter definition",
            corner_radius=16,
        )
        definition_textbox.grid(row=3, column=0, sticky="ew")

        image_label = ctk.CTkLabel(
            form_frame,
            text="Illustration",
            font=self.dialog_label_font,
            text_color="#111827",
            anchor="w",
            justify="left",
        )
        image_label.grid(row=4, column=0, sticky="w", pady=(16, 8))

        image_input_frame = ctk.CTkFrame(
            form_frame,
            fg_color="#FFFFFF",
            border_color="#CBD5E1",
            border_width=2,
            corner_radius=16,
        )
        image_input_frame.grid(row=5, column=0, sticky="ew")
        image_input_frame.grid_columnconfigure(0, weight=1)

        image_picker_frame = ctk.CTkFrame(
            image_input_frame,
            fg_color="transparent",
        )
        image_picker_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=8)
        image_picker_frame.grid_columnconfigure(0, weight=1)
        image_picker_frame.grid_columnconfigure(1, weight=0)

        image_status_label = ctk.CTkLabel(
            image_picker_frame,
            text="No image selected",
            font=self.body_font,
            text_color="#4B5563",
            anchor="w",
            justify="left",
            wraplength=260,
        )
        image_status_label.grid(row=0, column=0, sticky="w", padx=(0, 16))

        image_select_button = ctk.CTkButton(
            image_picker_frame,
            text="Choose File",
            font=self.button_font,
            fg_color="#1D6CFF",
            hover_color="#0F55C9",
            command=self.on_add_select_image,
            width=140,
            height=36,
            corner_radius=14,
        )
        image_select_button.grid(row=0, column=1, sticky="e")

        image_feedback_label = ctk.CTkLabel(
            form_frame,
            text="",
            font=self.body_font,
            text_color="#DC2626",
            anchor="w",
            justify="left",
            wraplength=360,
        )
        image_feedback_label.grid(row=6, column=0, sticky="w", pady=(8, 0), padx=4)

        buttons_frame = ctk.CTkFrame(
            container,
            fg_color="transparent",
        )
        buttons_frame.grid(row=2, column=0, sticky="ew", pady=(0, 28), padx=20)
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=0)
        buttons_frame.grid_columnconfigure(2, weight=0)
        buttons_frame.grid_columnconfigure(3, weight=1)

        cancel_button = ctk.CTkButton(
            buttons_frame,
            text="Cancel",
            font=self.cancel_button_font,
            fg_color="#E5E7EB",
            text_color="#FFFFFF",
            hover_color="#CBD5E1",
            command=self.close_add_modal,
            width=130,
            height=46,
            corner_radius=14,
        )
        cancel_button.grid(row=0, column=1, sticky="e", padx=(0, 32))

        save_button = ctk.CTkButton(
            buttons_frame,
            text="Save",
            font=self.button_font,
            fg_color="#1D6CFF",
            hover_color="#0F55C9",
            command=self.handle_add_question_save,
            width=130,
            height=46,
            corner_radius=14,
        )
        save_button.grid(row=0, column=2, sticky="w", padx=(32, 0))

        self.add_modal = modal
        self.add_concept_entry = concept_entry
        self.add_definition_textbox = definition_textbox
        self.add_image_display_label = image_status_label
        self.add_image_feedback_label = image_feedback_label
        self.add_selected_image_source_path = None

        modal.protocol("WM_DELETE_WINDOW", self.close_add_modal)
        modal.bind("<Escape>", self.close_add_modal)

        modal.update_idletasks()
        try:
            concept_entry.focus_set()
        except tk.TclError:
            pass

        screen_width = modal.winfo_screenwidth()
        screen_height = modal.winfo_screenheight()

        parent_width = (
            root.winfo_width() if root and root.winfo_width() > 1 else screen_width
        )
        parent_height = (
            root.winfo_height() if root and root.winfo_height() > 1 else screen_height
        )

        target_width = max(480, int(parent_width * 0.5))
        target_height = max(460, int(parent_height * 0.6))

        width = min(target_width, screen_width - 80)
        height = min(target_height, screen_height - 80)

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

    def on_add_select_image(self):
        if not self.add_modal or not self.add_modal.winfo_exists():
            return

        try:
            initial_dir = (
                str(self.IMAGES_DIR) if self.IMAGES_DIR.exists() else str(Path.home())
            )
        except (OSError, RuntimeError):
            initial_dir = None

        try:
            file_path = filedialog.askopenfilename(
                parent=self.add_modal,
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
        extension = source_path.suffix.lower()
        allowed_extensions = {".png", ".jpg", ".jpeg", ".gif", ".bmp"}

        feedback_label = (
            self.add_image_feedback_label
            if self.add_image_feedback_label
            and self.add_image_feedback_label.winfo_exists()
            else None
        )
        status_label = (
            self.add_image_display_label
            if self.add_image_display_label
            and self.add_image_display_label.winfo_exists()
            else None
        )

        if extension not in allowed_extensions:
            if feedback_label:
                feedback_label.configure(
                    text="Unsupported file type selected. Please choose a PNG or JPG image.",
                    text_color="#DC2626",
                )
            if status_label:
                status_label.configure(text="No image selected", text_color="#4B5563")
            self.add_selected_image_source_path = None
            return

        display_name = source_path.name
        max_display_length = 60
        if len(display_name) > max_display_length:
            display_name = f"{display_name[:28]}...{display_name[-24:]}"

        if status_label:
            status_label.configure(text=display_name, text_color="#111827")

        if feedback_label:
            feedback_label.configure(
                text="Image ready to import.",
                text_color="#047857",
            )

        self.add_selected_image_source_path = str(source_path)

    def close_add_modal(self):
        if self.add_modal and self.add_modal.winfo_exists():
            try:
                self.add_modal.grab_release()
            except tk.TclError:
                pass
            self.add_modal.destroy()
        self.add_modal = None
        self.add_concept_entry = None
        self.add_definition_textbox = None
        self.add_image_display_label = None
        self.add_image_feedback_label = None
        self.add_selected_image_source_path = None

    def handle_add_question_save(self):
        if not self.add_concept_entry or not self.add_concept_entry.winfo_exists():
            return

        if (
            not self.add_definition_textbox
            or not self.add_definition_textbox.winfo_exists()
        ):
            return

        title = (self.add_concept_entry.get() or "").strip()

        definition_widget = self.add_definition_textbox
        definition_value = ""

        if definition_widget:
            try:
                definition_value = definition_widget.get()
            except (TypeError, tk.TclError):
                definition_value = ""

        definition = (definition_value or "").strip()

        if not title:
            messagebox.showwarning(
                "Missing Information", "Please enter a title for the question."
            )
            try:
                self.add_concept_entry.focus_set()
            except tk.TclError:
                pass
            return

        if not definition:
            messagebox.showwarning(
                "Missing Information", "Please provide a definition for the question."
            )
            try:
                self.add_definition_textbox.focus_set()
            except tk.TclError:
                pass
            return

        normalized_title = title.lower()
        for existing in self.questions:
            existing_title = (existing.get("title") or "").strip().lower()
            if existing_title == normalized_title:
                messagebox.showwarning(
                    "Duplicate Question",
                    "A question with this title already exists. Please use a different title.",
                )
                try:
                    self.add_concept_entry.focus_set()
                    self.add_concept_entry.select_range(0, tk.END)
                except tk.TclError:
                    pass
                return

        if not self.add_selected_image_source_path:
            messagebox.showwarning(
                "Missing Information",
                "Please choose an illustration for the question.",
            )
            if (
                self.add_image_feedback_label
                and self.add_image_feedback_label.winfo_exists()
            ):
                self.add_image_feedback_label.configure(
                    text="Select an image before saving.",
                    text_color="#DC2626",
                )
            return

        source_image_path = Path(self.add_selected_image_source_path)
        if not source_image_path.exists():
            messagebox.showerror(
                "Image Not Found",
                "The selected image could not be located. Please choose a different file.",
            )
            if (
                self.add_image_feedback_label
                and self.add_image_feedback_label.winfo_exists()
            ):
                self.add_image_feedback_label.configure(
                    text="Selected file is no longer available.",
                    text_color="#DC2626",
                )
            self.add_selected_image_source_path = None
            if (
                self.add_image_display_label
                and self.add_image_display_label.winfo_exists()
            ):
                self.add_image_display_label.configure(
                    text="No image selected", text_color="#4B5563"
                )
            return

        try:
            resolved_images_dir = self.IMAGES_DIR.resolve()
            resolved_source = source_image_path.resolve()
        except OSError:
            resolved_images_dir = self.IMAGES_DIR
            resolved_source = source_image_path

        relative_image_path = None
        destination_path = None

        try:
            relative_sub_path = resolved_source.relative_to(resolved_images_dir)
            destination_path = resolved_source
            relative_image_path = Path("recursos") / "imagenes" / relative_sub_path
        except ValueError:
            destination_dir = self.IMAGES_DIR
            try:
                destination_dir.mkdir(parents=True, exist_ok=True)
            except OSError as error:
                messagebox.showerror(
                    "Image Folder Error",
                    f"Unable to create the images directory.\n\nDetails: {error}",
                )
                return

            candidate_name = source_image_path.name or "image.png"
            candidate_stem = source_image_path.stem or "image"
            candidate_suffix = source_image_path.suffix or ".png"

            destination_path = destination_dir / candidate_name
            copy_index = 1
            while destination_path.exists():
                destination_path = (
                    destination_dir / f"{candidate_stem}_{copy_index}{candidate_suffix}"
                )
                copy_index += 1

            try:
                shutil.copy2(source_image_path, destination_path)
            except OSError as error:
                messagebox.showerror(
                    "Image Copy Failed",
                    f"Unable to copy the selected image into the project.\n\nDetails: {error}",
                )
                return

            relative_image_path = Path("recursos") / "imagenes" / destination_path.name

        stored_image_path = (
            relative_image_path.as_posix()
            if relative_image_path is not None
            else destination_path.as_posix()
        )

        new_question = {
            "title": title,
            "definition": definition,
            "image": stored_image_path,
        }

        updated_questions = list(self.questions)
        updated_questions.append(new_question)

        if not self.save_questions(updated_questions):
            if self.add_modal and self.add_modal.winfo_exists():
                try:
                    self.add_modal.lift()
                    self.add_modal.focus_force()
                except tk.TclError:
                    pass
            return

        self.questions = updated_questions
        self.current_question = new_question
        self.current_image_path = stored_image_path

        if self.search_entry and self.search_entry.winfo_exists():
            try:
                self.search_entry.delete(0, tk.END)
            except tk.TclError:
                pass

        self.filtered_questions = list(self.questions)
        self.render_question_list()

        if self.selected_question_button:
            self.show_question_details(
                self.current_question, self.selected_question_button
            )

        self.close_add_modal()

    def show_delete_confirmation_modal(self):
        if not self.current_question:
            return

        if self.parent and not self.parent.winfo_exists():
            return

        if self.delete_modal and self.delete_modal.winfo_exists():
            try:
                self.delete_modal.lift()
                self.delete_modal.focus_force()
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
        modal.configure(fg_color="#F5F7FA")
        modal.grid_rowconfigure(0, weight=1)
        modal.grid_columnconfigure(0, weight=1)

        container = ctk.CTkFrame(
            modal,
            fg_color="#F5F7FA",
            corner_radius=0,
        )
        container.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(1, weight=1)

        header_frame = ctk.CTkFrame(
            container,
            fg_color="#202632",
            corner_radius=0,
            height=72,
        )
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 24), padx=0)
        header_frame.grid_propagate(False)
        header_frame.grid_columnconfigure(0, weight=1)
        header_frame.grid_rowconfigure(0, weight=1)

        header_label = ctk.CTkLabel(
            header_frame,
            text="Delete Question",
            font=self.dialog_title_font,
            text_color="#FFFFFF",
            anchor="center",
            justify="center",
        )
        header_label.grid(row=0, column=0, sticky="nsew", padx=24, pady=(28, 12))

        message_label = ctk.CTkLabel(
            container,
            text=(
                "Are you sure you want to delete this question? "
                "This action is irreversible."
            ),
            font=self.dialog_body_font,
            text_color="#111827",
            justify="center",
            anchor="center",
            wraplength=480,
        )
        message_label.grid(row=1, column=0, sticky="nsew", pady=(0, 20), padx=20)

        buttons_frame = ctk.CTkFrame(
            container,
            fg_color="transparent",
        )
        buttons_frame.grid(row=2, column=0, sticky="ew", pady=(0, 28), padx=20)
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=0)
        buttons_frame.grid_columnconfigure(2, weight=0)
        buttons_frame.grid_columnconfigure(3, weight=1)

        cancel_button = ctk.CTkButton(
            buttons_frame,
            text="Cancel",
            font=self.button_font,
            fg_color="#E5E7EB",
            text_color="#1F2937",
            hover_color="#CBD5E1",
            command=self.close_delete_modal,
            width=130,
            height=46,
            corner_radius=14,
        )
        cancel_button.grid(row=0, column=1, sticky="e", padx=(0, 32))

        confirm_button = ctk.CTkButton(
            buttons_frame,
            text="Delete",
            font=self.button_font,
            fg_color="#FF4F60",
            hover_color="#E53949",
            command=self.confirm_delete_question,
            width=130,
            height=46,
            corner_radius=14,
        )
        confirm_button.grid(row=0, column=2, sticky="w", padx=(32, 0))

        self.delete_modal = modal
        modal.protocol("WM_DELETE_WINDOW", self.close_delete_modal)
        modal.bind("<Escape>", self.close_delete_modal)

        modal.update_idletasks()
        try:
            confirm_button.focus_set()
        except tk.TclError:
            pass

        screen_width = modal.winfo_screenwidth()
        screen_height = modal.winfo_screenheight()

        parent_width = (
            root.winfo_width() if root and root.winfo_width() > 1 else screen_width
        )
        parent_height = (
            root.winfo_height() if root and root.winfo_height() > 1 else screen_height
        )

        target_width = max(480, int(parent_width * 0.5))
        target_height = max(340, int(parent_height * 0.5))

        width = min(target_width, screen_width - 80)
        height = min(target_height, screen_height - 80)

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

    def close_delete_modal(self, event=None):
        if self.delete_modal and self.delete_modal.winfo_exists():
            try:
                self.delete_modal.grab_release()
            except tk.TclError:
                pass
            try:
                self.delete_modal.destroy()
            except tk.TclError:
                pass

        self.delete_modal = None
        if event:
            return "break"

    def confirm_delete_question(self):
        if not self.current_question:
            self.close_delete_modal()
            return

        question_to_delete = self.current_question
        target_index = None
        for index, candidate in enumerate(self.questions):
            if candidate is question_to_delete:
                target_index = index
                break

        if target_index is None:
            self.close_delete_modal()
            return

        updated_questions = list(self.questions)
        updated_questions.pop(target_index)

        if not self.save_questions(updated_questions):
            if self.delete_modal and self.delete_modal.winfo_exists():
                try:
                    self.delete_modal.lift()
                    self.delete_modal.focus_force()
                except tk.TclError:
                    pass
            return

        self.questions = updated_questions
        self.current_question = None
        self.filtered_questions = [
            question
            for question in self.filtered_questions
            if question is not question_to_delete
        ]
        self.clear_question_details()
        self.on_search_change()
        self.close_delete_modal()

    def on_definition_audio_pressed(self):
        if not self.current_question:
            return

        definition = (self.current_question.get("definition") or "").strip()
        if definition:
            self.tts.speak(definition)

    def return_to_menu(self):
        self.tts.stop()
        if self.on_return_callback:
            self.on_return_callback()

    def load_svg_image(self, svg_path, scale=1.0):
        try:
            svg_photo = TkSvgImage(file=str(svg_path), scale=scale)
            return ImageTk.getimage(svg_photo).convert("RGBA")
        except (FileNotFoundError, OSError, ValueError, RuntimeError):
            return None

    def ensure_audio_icon(self):
        if self.definition_audio_image:
            return

        svg_path = self.IMAGES_DIR / self.AUDIO_ICON_FILENAME
        pil_image = self.load_svg_image(svg_path, scale=self.SVG_RASTER_SCALE)

        if pil_image:
            self.definition_audio_image = ctk.CTkImage(
                light_image=pil_image,
                dark_image=pil_image,
                size=self.AUDIO_ICON_SIZE,
            )

    def ensure_search_icon(self):
        if self.search_icon_image:
            return

        svg_path = self.IMAGES_DIR / self.SEARCH_ICON_FILENAME
        pil_image = self.load_svg_image(svg_path, scale=self.SVG_RASTER_SCALE)

        if pil_image:
            resized_image = pil_image
            try:
                alpha_channel = pil_image.getchannel("A")
                bbox = alpha_channel.getbbox()
            except (ValueError, OSError, AttributeError):
                bbox = None

            cropped_image = pil_image.crop(bbox) if bbox else pil_image

            if cropped_image.size != self.SEARCH_ICON_SIZE:
                resample = getattr(Image.Resampling, "LANCZOS", 1)
                resized_image = cropped_image.resize(self.SEARCH_ICON_SIZE, resample)
            else:
                resized_image = cropped_image

            self.search_icon_image = ctk.CTkImage(
                light_image=resized_image,
                dark_image=resized_image,
                size=self.SEARCH_ICON_SIZE,
            )

    def resolve_image_path(self, image_path):
        if not image_path:
            return None

        candidate = Path(image_path)
        if not candidate.is_absolute():
            candidate = Path(__file__).resolve().parent.parent / candidate

        return candidate if candidate.exists() else None

    def create_detail_ctk_image(self, image_file):
        try:
            with Image.open(image_file) as img:
                prepared_image = img.convert("RGBA").copy()
        except (FileNotFoundError, OSError, ValueError):
            return None

        width, height = prepared_image.size
        if width <= 0 or height <= 0:
            return None

        # Calculate scale to fit within max size
        max_width, max_height = self.DETAIL_IMAGE_MAX_SIZE
        scale = min(max_width / width, max_height / height, 1)

        if scale < 1:
            new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
            resample = getattr(Image.Resampling, "LANCZOS", 1)
            prepared_image = prepared_image.resize(new_size, resample)

        return ctk.CTkImage(
            light_image=prepared_image,
            dark_image=prepared_image,
            size=prepared_image.size,
        )

    def update_detail_image(self):
        if not self.detail_image_label or not self.detail_image_label.winfo_exists():
            return

        # Try to load and display image
        resolved_path = self.resolve_image_path(self.current_image_path)
        loaded_image = (
            self.create_detail_ctk_image(resolved_path) if resolved_path else None
        )

        try:
            if loaded_image:
                self.detail_image_label.configure(image=loaded_image, text="")
                self.detail_image = loaded_image
                self.detail_image_label.image = loaded_image
            else:
                self.detail_image_label.configure(
                    image=None, text="Image not available"
                )
                self.detail_image = None
                self.detail_image_label.image = None
        except tk.TclError:
            pass

    def show_question_details(self, question, button):
        self.tts.stop()

        # Show detail panel if hidden
        if not self.detail_visible:
            self.detail_container.grid()
            self.detail_visible = True

        # Update button selection states
        if (
            self.selected_question_button
            and self.selected_question_button is not button
        ):
            self.apply_default_button_style(self.selected_question_button)

        self.apply_selected_button_style(button)
        self.selected_question_button = button

        # Update detail content
        title = question.get("title", "")
        raw_definition = (question.get("definition") or "").strip()
        definition = raw_definition or "No definition available yet."

        self.current_question = question
        self.current_image_path = question.get("image", "")
        self.update_detail_image()

        # Enable/disable audio button based on definition availability
        if self.definition_audio_button:
            self.definition_audio_button.configure(
                state="normal" if raw_definition else "disabled"
            )

        self.detail_title_label.configure(text=title)
        self.detail_definition_label.configure(text=definition)

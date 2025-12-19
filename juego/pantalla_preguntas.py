import tkinter as tk
from pathlib import Path
from tkinter import messagebox
from types import SimpleNamespace

import customtkinter as ctk

from juego.image_handler import ImageHandler
from juego.pantalla_preguntas_config import (
    SCREEN_BASE_DIMENSIONS,
    SCREEN_COLORS,
    SCREEN_DEFINITION_PADDING_PROFILE,
    SCREEN_DEFINITION_STACK_BREAKPOINT,
    SCREEN_DEFINITION_WRAP_FILL_PROFILE,
    SCREEN_DEFINITION_WRAP_LIMITS,
    SCREEN_DEFINITION_WRAP_PIXEL_PROFILE,
    SCREEN_DETAIL_WEIGHT,
    SCREEN_FONT_SPECS,
    SCREEN_GLOBAL_SCALE_FACTOR,
    SCREEN_HEADER_SIZE_MULTIPLIER,
    SCREEN_ICONS,
    SCREEN_LOW_RES_SCALE_PROFILE,
    SCREEN_RESIZE_DELAY,
    SCREEN_SCALE_LIMITS,
    SCREEN_SIDEBAR_WEIGHT,
    SCREEN_SIDEBAR_WIDTH_PROFILE,
    SCREEN_SIZES,
    SCREEN_VIEWPORT_WRAP_RATIO_PROFILE,
    QuestionPersistenceError,
    QuestionRepository,
    ScreenFontRegistry,
)
from juego.pantalla_preguntas_layout import QuestionScreenLayoutMixin
from juego.preguntas_modales import (
    AddQuestionModal,
    DeleteConfirmationModal,
    EditQuestionModal,
)
from juego.responsive_helpers import (
    LayoutCalculator,
    ResponsiveScaler,
    SizeStateCalculator,
)
from juego.tts_service import TTSService


class QuestionScreenViewMixin(QuestionScreenLayoutMixin):
    def _init_question_screen_view(self):
        self.selected_question_button = None
        self.detail_visible = False
        self.search_entry = None
        self.list_container = None
        self.detail_container = None
        self.detail_title_label = None
        self.detail_definition_textbox = None
        self.detail_image_label = None
        self.definition_audio_button = None
        self.main_frame = None
        self.header_frame = None
        self.menu_button = None
        self.header_title_label = None
        self.sidebar_frame = None
        self.controls_frame = None
        self.search_wrapper = None
        self.search_icon_label = None
        self.add_button = None
        self.list_frame_padding = 8
        self.list_frame_corner_radius = 24
        self.detail_header_frame = None
        self.detail_body_frame = None
        self.detail_content_frame = None
        self.definition_row = None
        self.detail_action_buttons = []
        self.divider_frame = None
        self.current_detail_image = None
        self.render_metric_snapshot = None
        self.detail_scroll_height = 0
        self.definition_pad = 0
        self.definition_button_width = 0
        self.definition_button_gap = 16
        self.definition_layout_inline = True
        self._detail_scrollbar_visible = None
        self._detail_scrollbar_manager = None
        self._detail_scroll_update_job = None
        self.header_pad = 0
        self.body_pad = 0
        self.current_window_width = self.BASE_DIMENSIONS[0]
        self.current_window_height = self.BASE_DIMENSIONS[1]
        self.current_modal = None

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

        self.icon_base_sizes = {
            "audio": self.SIZES["audio_icon"],
            "search": self.SIZES["search_icon"],
            "back": self.SIZES["back_icon"],
        }
        self.icon_cache = {}

        self.size_state = dict(self.SIZES)
        self.current_scale = 1.0
        self._resize_job = None

        for widget in self.parent.winfo_children():
            widget.destroy()
        self.build_ui()

        self.apply_responsive()

        self.parent.bind("<Button-1>", self.handle_global_click, add="+")
        self.parent.bind("<Configure>", self.on_resize)

    def clear_search(self):
        if self.search_entry and self.search_entry.winfo_exists():
            try:
                self.search_entry.delete(0, tk.END)
            except tk.TclError:
                pass

    def build_ui(self):
        self.parent.grid_rowconfigure(0, weight=1)
        self.parent.grid_columnconfigure(0, weight=1)

        self.main_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.grid_rowconfigure(1, weight=1)
        column_layout = {
            0: {"weight": self.SIDEBAR_WEIGHT, "minsize": 280},
            1: {"weight": 0, "minsize": 2},
            2: {"weight": self.DETAIL_WEIGHT, "minsize": 220},
        }
        for col, cfg in column_layout.items():
            self.main_frame.grid_columnconfigure(col, **cfg)

        self.build_header(self.main_frame)
        self.build_detail_panel(self.main_frame)
        self.build_sidebar(self.main_frame)
        self.build_divider(self.main_frame)

    def build_header(self, parent):
        c = self.COLORS
        self.header_frame = ctk.CTkFrame(
            parent, fg_color=c["header_bg"], corner_radius=0
        )
        self.header_frame.grid(row=0, column=0, columnspan=3, sticky="ew")
        self.header_frame.grid_columnconfigure(1, weight=1)

        self.menu_button = ctk.CTkButton(
            self.header_frame,
            text="Menu",
            font=self.header_button_font or self.button_font,
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
        )
        self.menu_button.grid(row=0, column=0, padx=(24, 16), pady=(28, 32), sticky="w")

        self.header_title_label = ctk.CTkLabel(
            self.header_frame,
            text="Manage Questions",
            font=self.title_font,
            text_color=c["text_white"],
            anchor="center",
        )
        self.header_title_label.grid(
            row=0, column=1, padx=32, pady=(28, 32), sticky="nsew"
        )

    def build_sidebar(self, parent):
        self.sidebar_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.sidebar_frame.grid(row=1, column=0, sticky="nsew", padx=(32, 12), pady=32)
        self.sidebar_frame.grid_rowconfigure(1, weight=1)
        self.sidebar_frame.grid_columnconfigure(0, weight=1)

        self.build_controls(self.sidebar_frame)
        self.build_question_list_container(self.sidebar_frame)

    def build_controls(self, parent):
        c = self.COLORS
        self.controls_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.controls_frame.grid(row=0, column=0, sticky="ew")
        self.controls_frame.grid_columnconfigure(0, weight=1)

        self.search_wrapper = ctk.CTkFrame(
            self.controls_frame, fg_color=c["search_bg"], corner_radius=18
        )
        self.search_wrapper.grid(row=0, column=0, padx=(16, 12), pady=16, sticky="ew")
        self.search_wrapper.grid_columnconfigure(1, weight=1)

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

        self.search_icon_label = ctk.CTkLabel(self.search_wrapper, **icon_config)
        self.search_icon_label.grid(row=0, column=0, padx=(12, 4), sticky="w")

        self.search_entry = ctk.CTkEntry(
            self.search_wrapper,
            placeholder_text="Search...",
            placeholder_text_color=c["text_placeholder"],
            fg_color="transparent",
            text_color=c["text_white"],
            font=self.search_font,
            corner_radius=0,
            height=42,
            border_width=0,
        )
        self.search_entry.grid(row=0, column=1, padx=(4, 18), pady=4, sticky="nsew")
        for event in ("<KeyRelease>", "<<Paste>>", "<<Cut>>"):
            self.search_entry.bind(event, lambda e: self.handle_search())

        self.add_button = ctk.CTkButton(
            self.controls_frame,
            text="Add",
            font=self.button_font,
            fg_color=c["primary"],
            hover_color=c["primary_hover"],
            command=self.on_add_clicked,
            width=96,
            height=42,
            corner_radius=12,
        )
        self.add_button.grid(row=0, column=1, padx=(0, 16), pady=16)

    def build_question_list_container(self, parent):
        self.list_container = ctk.CTkFrame(parent, fg_color="transparent")
        self.list_container.grid(row=1, column=0, sticky="nsew", pady=(20, 0))
        self.list_container.grid_columnconfigure(0, weight=1)
        self.list_container.grid_rowconfigure(0, weight=1)

        self.render_question_list()

    def build_divider(self, parent):
        self.divider_frame = ctk.CTkFrame(
            parent,
            fg_color=self.COLORS["border_light"],
            corner_radius=0,
            width=2,
        )
        self.divider_frame.grid(row=1, column=1, sticky="ns", pady=32)

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

        self.detail_container.grid_remove()
        self.detail_visible = False

    def build_detail_header(self):
        c = self.COLORS
        self.detail_header_frame = ctk.CTkFrame(
            self.detail_container, fg_color="transparent"
        )
        self.detail_header_frame.grid(
            row=0, column=0, sticky="ew", padx=24, pady=(24, 12)
        )
        self.detail_header_frame.grid_columnconfigure(0, weight=1)

        self.detail_title_label = ctk.CTkLabel(
            self.detail_header_frame,
            text="",
            font=self.detail_title_font,
            text_color=c["text_dark"],
            anchor="w",
            wraplength=600,
        )
        self.detail_title_label.grid(row=0, column=0, sticky="w", padx=(12, 0))

        self.detail_action_buttons = []
        for col, (text, fg, hover, cmd) in enumerate(
            [
                ("Edit", c["secondary"], c["secondary_hover"], self.on_edit_clicked),
                ("Delete", c["danger"], c["danger_hover"], self.on_delete_clicked),
            ],
            start=1,
        ):
            button = ctk.CTkButton(
                self.detail_header_frame,
                text=text,
                font=self.question_font,
                fg_color=fg,
                hover_color=hover,
                command=cmd,
                width=110,
                height=44,
                corner_radius=12,
            )
            button.grid(row=0, column=col, padx=(12, 12 if col == 1 else 0), sticky="e")
            self.detail_action_buttons.append(button)

    def build_detail_body(self):
        c = self.COLORS
        self.detail_body_frame = ctk.CTkFrame(
            self.detail_container, fg_color="transparent"
        )
        self.detail_body_frame.grid(
            row=1, column=0, sticky="nsew", padx=24, pady=(0, 24)
        )
        self.detail_body_frame.grid_rowconfigure(0, weight=1)
        self.detail_body_frame.grid_columnconfigure(0, weight=1)

        self.detail_content_frame = ctk.CTkFrame(
            self.detail_body_frame, fg_color="transparent", height=520
        )
        self.detail_content_frame.grid(row=0, column=0, sticky="nsew")
        self.detail_content_frame.grid_columnconfigure(0, weight=1)
        self.detail_content_frame.grid_rowconfigure(1, weight=1)

        self.detail_image_label = ctk.CTkLabel(
            self.detail_content_frame,
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

        self.definition_row = ctk.CTkFrame(
            self.detail_content_frame, fg_color="transparent"
        )
        self.definition_row.grid(row=1, column=0, sticky="nsew", padx=32, pady=(32, 0))
        self.definition_row.grid_columnconfigure(1, weight=1)
        self.definition_row.grid_rowconfigure(0, weight=1)

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

        self.definition_audio_button = ctk.CTkButton(
            self.definition_row, **audio_config
        )
        self.definition_audio_button.grid(row=0, column=0, sticky="nw", padx=(0, 16))

        self.detail_definition_textbox = ctk.CTkTextbox(
            self.definition_row,
            font=self.body_font,
            text_color=c["text_medium"],
            fg_color="transparent",
            wrap="word",
            height=100,
            activate_scrollbars=False,
            border_width=0,
        )
        self.detail_definition_textbox.grid(row=0, column=1, sticky="nsew")
        self.detail_definition_textbox.configure(state="disabled")
        self.queue_detail_scroll_update()

    def queue_detail_scroll_update(self):
        if not self.parent or not self.parent.winfo_exists():
            return
        if self._detail_scroll_update_job:
            try:
                self.parent.after_cancel(self._detail_scroll_update_job)
            except tk.TclError:
                pass
            self._detail_scroll_update_job = None
        try:
            self._detail_scroll_update_job = self.parent.after_idle(
                self.update_detail_scrollbar_visibility
            )
        except tk.TclError:
            self._detail_scroll_update_job = None
            self.update_detail_scrollbar_visibility()

    def update_detail_scrollbar_visibility(self):
        self._detail_scroll_update_job = None
        textbox = self.detail_definition_textbox
        if not textbox or not textbox.winfo_exists():
            return

        scrollbar = self._get_textbox_scrollbar(textbox)
        if not scrollbar or not scrollbar.winfo_exists():
            return

        target = self._get_textbox_scroll_target(textbox)
        if not target:
            return

        try:
            textbox.update_idletasks()
            _first, last = target.yview()
        except (tk.TclError, AttributeError, TypeError, ValueError):
            return

        needs_scroll = last < 0.999
        self._set_detail_scrollbar_visible(needs_scroll)

    def _set_detail_scrollbar_visible(self, visible):
        if self._detail_scrollbar_visible is visible:
            return

        scrollbar = self._get_textbox_scrollbar(self.detail_definition_textbox)
        if not scrollbar or not scrollbar.winfo_exists():
            return

        manager = self._detail_scrollbar_manager or scrollbar.winfo_manager()
        if not manager:
            manager = "grid"
        self._detail_scrollbar_manager = manager

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

        self._detail_scrollbar_visible = visible

    def _get_textbox_scrollbar(self, textbox):
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

    def _get_textbox_scroll_target(self, textbox):
        if not textbox:
            return None
        target = getattr(textbox, "_textbox", None)
        if target and hasattr(target, "yview"):
            return target
        if hasattr(textbox, "yview"):
            return textbox
        return None

    def _create_list_frame_container(self, is_scrollable):
        c = self.COLORS

        outer_frame = ctk.CTkFrame(
            self.list_container,
            fg_color=c["bg_light"],
            border_width=1,
            border_color=c["border_light"],
            corner_radius=self.list_frame_corner_radius,
        )
        outer_frame.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=self.list_frame_padding,
            pady=self.list_frame_padding,
        )
        outer_frame.grid_columnconfigure(0, weight=1)
        outer_frame.grid_rowconfigure(0, weight=1)

        frame_config = {
            "fg_color": "transparent",
            "border_width": 0,
            "corner_radius": 0,
        }
        FrameClass = ctk.CTkScrollableFrame if is_scrollable else ctk.CTkFrame
        list_frame = FrameClass(outer_frame, **frame_config)

        inner_padding = 4
        list_frame.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=inner_padding,
            pady=inner_padding,
        )
        list_frame.grid_columnconfigure(0, weight=1)
        inner_frame = getattr(list_frame, "_scrollable_frame", None)
        if inner_frame:
            try:
                inner_frame.grid_columnconfigure(0, weight=1)
            except tk.TclError:
                pass

        return list_frame

    def _show_empty_list_state(self, list_frame, has_search_query):
        c = self.COLORS
        empty_text = (
            "No questions match your search."
            if has_search_query
            else "No questions available."
        )
        ctk.CTkLabel(
            list_frame,
            text=empty_text,
            font=self.body_font,
            text_color=c["text_lighter"],
        ).grid(row=1, column=0, padx=24, pady=(12, 24))

    def _create_question_button(self, parent, question, is_selected, button_config):
        c = self.COLORS
        button = ctk.CTkButton(
            parent,
            text=question.get("title", ""),
            font=self.question_font,
            text_color=c["text_white"] if is_selected else c["question_text"],
            fg_color=c["question_selected"] if is_selected else c["question_bg"],
            hover_color=(
                c["question_selected"] if is_selected else c["question_hover"]
            ),
            border_width=0,
            **button_config,
        )

        button.configure(
            command=lambda q=question, b=button: self.on_question_selected(q, b)
        )
        return button

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
        list_frame = self._create_list_frame_container(is_scrollable)

        if not questions:
            self._show_empty_list_state(list_frame, search_query.strip())
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

            button = self._create_question_button(
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


class ManageQuestionsScreen(QuestionScreenViewMixin):
    BASE_DIMENSIONS = SCREEN_BASE_DIMENSIONS
    SCALE_LIMITS = SCREEN_SCALE_LIMITS
    RESIZE_DELAY = SCREEN_RESIZE_DELAY
    GLOBAL_SCALE_FACTOR = SCREEN_GLOBAL_SCALE_FACTOR
    HEADER_SIZE_MULTIPLIER = SCREEN_HEADER_SIZE_MULTIPLIER
    SIDEBAR_WEIGHT = SCREEN_SIDEBAR_WEIGHT
    DETAIL_WEIGHT = SCREEN_DETAIL_WEIGHT

    ICONS = SCREEN_ICONS
    COLORS = SCREEN_COLORS
    SIZES = SCREEN_SIZES
    DEFINITION_PADDING_PROFILE = SCREEN_DEFINITION_PADDING_PROFILE
    DEFINITION_WRAP_FILL_PROFILE = SCREEN_DEFINITION_WRAP_FILL_PROFILE
    DEFINITION_WRAP_PIXEL_PROFILE = SCREEN_DEFINITION_WRAP_PIXEL_PROFILE
    DEFINITION_WRAP_LIMITS = SCREEN_DEFINITION_WRAP_LIMITS
    DEFINITION_STACK_BREAKPOINT = SCREEN_DEFINITION_STACK_BREAKPOINT
    VIEWPORT_WRAP_RATIO_PROFILE = SCREEN_VIEWPORT_WRAP_RATIO_PROFILE
    SIDEBAR_WIDTH_PROFILE = SCREEN_SIDEBAR_WIDTH_PROFILE
    LOW_RES_SCALE_PROFILE = SCREEN_LOW_RES_SCALE_PROFILE
    FONT_SPECS = SCREEN_FONT_SPECS

    BASE_DIR = Path(__file__).resolve().parent.parent
    QUESTIONS_FILE = BASE_DIR / "datos" / "preguntas.json"
    IMAGES_DIR = BASE_DIR / "recursos" / "imagenes"
    AUDIO_DIR = BASE_DIR / "recursos" / "audio"

    def __init__(self, parent, on_return_callback=None, tts_service=None):
        self.parent = parent
        self.on_return_callback = on_return_callback

        self.font_registry = ScreenFontRegistry(self.FONT_SPECS)
        self.font_registry.attach_attributes(self)
        self.font_base_sizes = dict(self.font_registry.base_sizes)
        self.font_min_sizes = dict(self.font_registry.min_sizes)

        self.scaler = ResponsiveScaler(
            base_dimensions=self.BASE_DIMENSIONS,
            scale_limits=self.SCALE_LIMITS,
            global_scale_factor=self.GLOBAL_SCALE_FACTOR,
        )

        profiles = {
            "sidebar_width": self.SIDEBAR_WIDTH_PROFILE,
            "definition_padding": self.DEFINITION_PADDING_PROFILE,
            "wrap_fill": self.DEFINITION_WRAP_FILL_PROFILE,
        }

        self.size_calc = SizeStateCalculator(self.scaler, self.SIZES, profiles)
        self.layout_calc = LayoutCalculator(self.scaler, profiles)

        self.tts = tts_service or TTSService(self.AUDIO_DIR)
        self.image_handler = ImageHandler(self.IMAGES_DIR)
        self.repository = QuestionRepository(self.QUESTIONS_FILE)

        self.refresh_question_cache()
        self.filtered_questions = list(self.questions)

        self.current_modal = None
        self.current_question = (
            self.filtered_questions[0] if self.filtered_questions else None
        )
        self._init_question_screen_view()

    def refresh_question_cache(self):
        self.questions = list(self.repository.questions)

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

    def filter_questions(self, query):
        query = (query or "").strip().lower()
        self.filtered_questions = (
            [q for q in self.questions if query in q.get("title", "").lower()]
            if query
            else list(self.questions)
        )

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

import tkinter as tk

import customtkinter as ctk

from juego.pantalla_preguntas_orden import QuestionScreenLayoutMixin


class QuestionScreenUIMixin(QuestionScreenLayoutMixin):

    def init_view_state(self):
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
        self.detail_scrollbar_visible = None
        self.detail_scrollbar_manager = None
        self.detail_scroll_update_job = None
        self.header_pad = 0
        self.body_pad = 0
        self.current_window_width = self.BASE_DIMENSIONS[0]
        self.current_window_height = self.BASE_DIMENSIONS[1]
        self.current_modal = None

    def init_icons(self):
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

    def init_scale_state(self):
        self.size_state = dict(self.SIZES)
        self.current_scale = 1.0
        self.resize_job = None

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

    def create_list_frame_container(self, is_scrollable):
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

    def show_empty_list_state(self, list_frame, has_search_query):
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

    def create_question_button(self, parent, question, is_selected, button_config):
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

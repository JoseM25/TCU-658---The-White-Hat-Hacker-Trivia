import customtkinter as ctk


class ManageQuestionsScreen:
    HEADER_TEXT = "Manage Questions"
    QUESTIONS = [
        "Cracker",
        "Modder",
        "Malware",
        "Exploit",
        "Brute Force",
        "Worm",
        "Pirate",
        "Tracing",
    ]
    MAX_VISIBLE_QUESTIONS = 6

    def __init__(self, parent, on_return_callback=None):
        self.parent = parent
        self.on_return_callback = on_return_callback
        self.placeholder_visible = False

        for widget in self.parent.winfo_children():
            widget.destroy()

        self.title_font = ctk.CTkFont(
            family="Poppins ExtraBold",
            size=38,
            weight="bold",
        )
        self.body_font = ctk.CTkFont(family="Poppins Medium", size=18)
        self.button_font = ctk.CTkFont(family="Poppins SemiBold", size=16)
        self.question_font = ctk.CTkFont(
            family="Poppins SemiBold",
            size=18,
            weight="bold",
        )

        self.build_ui()

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
        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header,
            text=self.HEADER_TEXT,
            font=self.title_font,
            text_color="#FFFFFF",
            anchor="center",
            justify="center",
        )
        title.grid(row=0, column=0, padx=32, pady=(28, 32), sticky="nsew")

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

        placeholder = ctk.CTkFrame(
            self.main,
            fg_color="#EEF2F8",
            corner_radius=16,
        )
        placeholder.grid(row=1, column=2, sticky="nsew", padx=(12, 32), pady=32)
        placeholder.grid_rowconfigure(0, weight=1)
        placeholder.grid_columnconfigure(0, weight=1)

        self.placeholder_label = ctk.CTkLabel(
            placeholder,
            text="Question details will appear here.",
            font=self.body_font,
            text_color="#6B7280",
        )
        self.placeholder_label.grid(row=0, column=0, padx=24, pady=24, sticky="nsew")

        self.placeholder = placeholder
        self.placeholder.grid_remove()
        self.placeholder_visible = False

    def build_controls(self, container):
        controls = ctk.CTkFrame(
            container,
            fg_color="transparent",
        )
        controls.grid(row=0, column=0, sticky="ew")
        controls.grid_columnconfigure(0, weight=1)
        controls.grid_columnconfigure(1, weight=0)
        search_entry = ctk.CTkEntry(
            controls,
            placeholder_text="Search...",
            placeholder_text_color="#F5F7FA",
            fg_color="#D1D8E0",
            font=self.body_font,
            corner_radius=18,
            height=42,
            border_width=0,
        )
        search_entry.grid(row=0, column=0, padx=(16, 12), pady=16, sticky="ew")

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

    def build_question_list(self, container):
        needs_scrollbar = len(self.QUESTIONS) > self.MAX_VISIBLE_QUESTIONS
        frame_class = ctk.CTkScrollableFrame if needs_scrollbar else ctk.CTkFrame

        list_frame = frame_class(
            container,
            fg_color="#F5F7FA",
            border_width=1,
            border_color="#D2DAE6",
            corner_radius=24,
        )
        list_frame.grid(row=1, column=0, sticky="nsew", pady=(20, 0))
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, minsize=24)

        for index, question in enumerate(self.QUESTIONS, start=1):
            button = ctk.CTkButton(
                list_frame,
                text=question,
                font=self.question_font,
                text_color="#1F2937",
                fg_color="transparent",
                hover_color="#E2E8F0",
                border_width=0,
                corner_radius=12,
                command=lambda q=question: self.show_question_details(q),
            )
            button.grid(
                row=index,
                column=0,
                sticky="nsew",
                padx=24,
                pady=(0 if index == 1 else 12, 12),
            )
            list_frame.grid_rowconfigure(index, weight=0)

        list_frame.grid_columnconfigure(0, weight=1)

    def on_add_pressed(self):
        # Placeholder for future add-question flow
        pass

    def return_to_menu(self):
        if self.on_return_callback:
            self.on_return_callback()

    def show_question_details(self, question):
        if not self.placeholder_visible:
            self.placeholder.grid()
            self.placeholder_visible = True

        self.placeholder_label.configure(
            text=f"Details for {question} will appear here soon."
        )

import json
import tempfile
from pathlib import Path

import customtkinter as ctk

# Screen base dimensions and scaling
SCREEN_BASE_DIMENSIONS = (1280, 720)
SCREEN_SCALE_LIMITS = (0.18, 1.90)
SCREEN_RESIZE_DELAY = 80
SCREEN_GLOBAL_SCALE_FACTOR = 0.55
SCREEN_HEADER_SIZE_MULTIPLIER = 1.18
SCREEN_SIDEBAR_WEIGHT = 24
SCREEN_DETAIL_WEIGHT = 76

SCREEN_ICONS = {"audio": "volume.svg", "search": "search.svg", "back": "arrow.svg"}

SCREEN_COLORS = {
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

SCREEN_SIZES = {
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

SCREEN_DEFINITION_PADDING_PROFILE = [
    (360, 8),
    (480, 10),
    (640, 12),
    (800, 14),
    (1024, 16),
    (1280, 18),
    (1600, 20),
    (1920, 22),
    (2560, 24),
    (3200, 26),
    (3840, 28),
]

SCREEN_DEFINITION_WRAP_FILL_PROFILE = [
    (360, 0.90),
    (480, 0.92),
    (640, 0.94),
    (800, 0.95),
    (1024, 0.96),
    (1280, 0.955),
    (1600, 0.945),
    (1920, 0.940),
    (2560, 0.935),
    (3200, 0.930),
    (3840, 0.925),
]

SCREEN_DEFINITION_WRAP_PIXEL_PROFILE = [
    (360, 320),
    (480, 420),
    (640, 560),
    (800, 720),
    (1024, 900),
    (1280, 1100),
    (1600, 1300),
    (1920, 1500),
    (2560, 1800),
    (3200, 2050),
    (3840, 2200),
]

SCREEN_DEFINITION_WRAP_LIMITS = (240, 2200)
SCREEN_DEFINITION_STACK_BREAKPOINT = 520

SCREEN_VIEWPORT_WRAP_RATIO_PROFILE = [
    (360, 0.75),
    (3840, 0.75),
]

SCREEN_SIDEBAR_WIDTH_PROFILE = [
    (720, 0.26),
    (960, 0.27),
    (1280, 0.28),
    (1440, 0.29),
    (1600, 0.30),
    (1920, 0.30),
    (2560, 0.31),
    (3200, 0.31),
    (3840, 0.32),
]

SCREEN_LOW_RES_SCALE_PROFILE = [
    (360, 0.62),
    (480, 0.72),
    (600, 0.82),
    (720, 1.00),
]

SCREEN_FONT_SPECS = {
    "title": ("Poppins ExtraBold", 44, "bold", 16),
    "body": ("Poppins Medium", 18, None, 9),
    "button": ("Poppins SemiBold", 16, "bold", 9),
    "header_button": ("Poppins SemiBold", 22, "bold", 12),
    "cancel_button": ("Poppins ExtraBold", 16, "bold", 9),
    "search": ("Poppins SemiBold", 18, "bold", 9),
    "question": ("Poppins SemiBold", 18, "bold", 9),
    "detail_title": ("Poppins ExtraBold", 38, "bold", 12),
    "dialog_title": ("Poppins SemiBold", 24, "bold", 12),
    "dialog_body": ("Poppins Medium", 16, None, 9),
    "dialog_label": ("Poppins SemiBold", 16, "bold", 9),
}


class ScreenFontRegistry:

    def __init__(self, specs):
        self._fonts = {}
        self.base_sizes = {}
        self.min_sizes = {}

        for name, (family, size, weight, min_size) in specs.items():
            font = (
                ctk.CTkFont(family=family, size=size, weight=weight)
                if weight
                else ctk.CTkFont(family=family, size=size)
            )
            self._fonts[name] = font
            self.base_sizes[name] = size
            self.min_sizes[name] = min_size or 10

    def get(self, name):
        return self._fonts[name]

    def items(self):
        return self._fonts.items()

    def as_dict(self):
        return dict(self._fonts)

    def attach_attributes(self, target):
        for name, font in self._fonts.items():
            setattr(target, f"{name}_font", font)


class QuestionPersistenceError(Exception):

    pass


class QuestionFileStorage:

    def __init__(self, json_path):
        self.json_path = Path(json_path)

    def load_questions(self):
        if not self.json_path.exists():
            return []

        try:
            raw_text = self.json_path.read_text(encoding="utf-8")
        except OSError as error:
            print(f"Warning: Unable to read {self.json_path}: {error}")
            return []

        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError:
            return []

        raw_questions = (
            data.get("questions", []) if hasattr(data, "get") else (data or [])
        )

        normalized = []
        for item in raw_questions:
            if not hasattr(item, "get"):
                continue
            title = (item.get("title") or "").strip()
            if not title:
                continue
            definition = (item.get("definition") or "").strip()
            image = (item.get("image") or "").strip()
            normalized.append(
                {"title": title, "definition": definition, "image": image}
            )

        return normalized

    def save_questions(self, questions):
        """Save questions atomically using a temp file and backup."""
        payload = {"questions": questions}
        backup_path = self.json_path.with_suffix(".json.bak")
        tmp_path = None

        try:
            self.json_path.parent.mkdir(parents=True, exist_ok=True)

            # Write to temp file first
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".json",
                dir=self.json_path.parent,
                delete=False,
                encoding="utf-8",
            ) as tmp:
                json.dump(payload, tmp, ensure_ascii=False, indent=2)
                tmp_path = Path(tmp.name)

            # Create backup of existing file (Windows requires removing target first)
            if self.json_path.exists():
                try:
                    if backup_path.exists():
                        backup_path.unlink()
                    self.json_path.rename(backup_path)
                except OSError:
                    # If backup fails, try direct overwrite
                    pass

            # Move temp to target (atomic on same filesystem)
            try:
                tmp_path.rename(self.json_path)
            except OSError:
                # On Windows cross-drive, fall back to copy + delete
                import shutil

                shutil.copy2(str(tmp_path), str(self.json_path))
                tmp_path.unlink()

            # Remove backup on success
            try:
                if backup_path.exists():
                    backup_path.unlink()
            except OSError:
                pass

        except OSError as error:
            # Try to restore from backup if save failed
            if backup_path.exists() and not self.json_path.exists():
                try:
                    backup_path.rename(self.json_path)
                except OSError:
                    pass
            # Clean up temp file if it exists
            if tmp_path and tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass
            raise QuestionPersistenceError(
                f"Unable to write {self.json_path}: {error}"
            ) from error


class QuestionRepository:

    def __init__(self, json_path):
        self.storage = QuestionFileStorage(json_path)
        self.questions = []
        self.load()

    def load(self):
        self.questions = self.storage.load_questions()
        return self.questions

    def save(self, questions):
        self.storage.save_questions(questions)
        self.questions = list(questions)
        return self.questions

    def add_question(self, title, definition, image_path):
        new_question = {"title": title, "definition": definition, "image": image_path}
        self.save([*self.questions, new_question])
        return new_question

    def update_question(self, old_question, title, definition, image_path):
        updated_question = {
            "title": title,
            "definition": definition,
            "image": image_path,
        }
        try:
            index = self.questions.index(old_question)
        except ValueError:
            index = None

        updated_questions = [q for q in self.questions if q is not old_question]
        insert_index = index if index is not None else len(updated_questions)
        updated_questions.insert(insert_index, updated_question)
        self.save(updated_questions)
        return self.questions[insert_index]

    def delete_question(self, question):
        try:
            index = self.questions.index(question)
        except ValueError:
            return False

        updated_questions = self.questions[:index] + self.questions[index + 1 :]
        self.save(updated_questions)
        return True

    def is_title_unique(self, title, exclude_question=None):
        normalized = (title or "").strip().lower()
        if not normalized:
            return False

        for question in self.questions:
            if exclude_question is not None and question is exclude_question:
                continue
            if (question.get("title") or "").strip().lower() == normalized:
                return False
        return True

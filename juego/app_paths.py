import os
import shutil
from pathlib import Path

APP_NAME = "The White Hat Hacker Trivia"


def get_app_root():
    return Path(__file__).resolve().parent.parent


def get_resource_root():
    return get_app_root()


def get_resource_dir():
    return get_resource_root() / "recursos"


def get_resource_images_dir():
    return get_resource_dir() / "imagenes"


def get_resource_audio_dir():
    return get_resource_dir() / "audio"


def get_default_questions_path():
    return get_resource_root() / "datos" / "preguntas.json"


def get_data_root():
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
    if base:
        return Path(base) / APP_NAME
    return get_app_root() / "userdata"


def get_user_images_dir():
    return get_data_root() / "recursos" / "imagenes"


def get_data_questions_path():
    return get_data_root() / "datos" / "preguntas.json"


def ensure_user_data():
    data_root = get_data_root()
    images_dir = get_user_images_dir()
    questions_path = get_data_questions_path()

    images_dir.mkdir(parents=True, exist_ok=True)

    if not questions_path.exists():
        questions_path.parent.mkdir(parents=True, exist_ok=True)
        default_questions = get_default_questions_path()
        if default_questions.exists():
            shutil.copy2(default_questions, questions_path)
        else:
            questions_path.write_text('{"questions": []}\n', encoding="utf-8")

    return data_root

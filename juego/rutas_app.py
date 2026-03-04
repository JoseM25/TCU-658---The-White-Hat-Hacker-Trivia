import json
import os
import shutil
import sys
from pathlib import Path

APP_NAME = "The White Hat Hacker Trivia"


def get_app_root():
    return Path(__file__).resolve().parent.parent


def is_frozen():
    return getattr(sys, "frozen", False)


def get_bundle_root():
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS", get_app_root()))
    return get_app_root()


def get_resource_root():
    if is_frozen():
        return get_data_root()
    return get_app_root()


def get_resource_dir():
    return get_resource_root() / "recursos"


def get_resource_images_dir():
    return get_resource_dir() / "imagenes"


def get_resource_audio_dir():
    return get_resource_dir() / "audio"


def get_default_questions_path():
    return get_bundle_root() / "datos" / "preguntas.json"


def get_data_root():
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
    if base:
        return Path(base) / APP_NAME

    # Respaldo al directorio home del usuario para asegurar permisos de escritura
    # (Evita fallos si está instalado en Program Files de solo lectura)
    return Path.home() / f".{APP_NAME.replace(' ', '_')}"


def get_user_images_dir():
    return get_data_root() / "recursos" / "imagenes"


def get_data_questions_path():
    return get_data_root() / "datos" / "preguntas.json"


def get_docs_dir():
    return get_data_root() / "docs"


def copy_missing_tree(source, destination):
    if not source.exists():
        return

    for src in source.rglob("*"):
        rel = src.relative_to(source)
        dst = destination / rel

        if src.is_dir():
            dst.mkdir(parents=True, exist_ok=True)
            continue

        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            shutil.copy2(src, dst)


def merge_default_questions(default_path, user_path):
    try:
        with open(default_path, "r", encoding="utf-8") as f:
            default_data = json.load(f)
            default_questions = default_data.get("questions", [])

        with open(user_path, "r", encoding="utf-8") as f:
            user_data = json.load(f)
            user_questions = user_data.get("questions", [])

        existing_titles = {q.get("title", "").strip().lower() for q in user_questions}

        added_count = 0
        for q in default_questions:
            title = q.get("title", "").strip()
            if title and title.lower() not in existing_titles:
                user_questions.append(q)
                added_count += 1

        if added_count > 0:
            user_data["questions"] = user_questions
            with open(user_path, "w", encoding="utf-8") as f:
                json.dump(user_data, f, indent=2, ensure_ascii=False)

    except (OSError, json.JSONDecodeError):
        # Si hay corrupción o error de E/S, se omite la fusión para no empeorar las cosas
        pass


def ensure_user_data():
    data_root = get_data_root()
    images_dir = get_user_images_dir()
    questions_path = get_data_questions_path()
    bundle_root = get_bundle_root()
    default_questions = get_default_questions_path()

    images_dir.mkdir(parents=True, exist_ok=True)

    if is_frozen():
        copy_missing_tree(bundle_root / "recursos", data_root / "recursos")
        copy_missing_tree(bundle_root / "datos", data_root / "datos")
        copy_missing_tree(bundle_root / "docs", data_root / "docs")

    if not questions_path.exists():
        questions_path.parent.mkdir(parents=True, exist_ok=True)
        if default_questions.exists():
            shutil.copy2(default_questions, questions_path)
        else:
            questions_path.write_text('{"questions": []}\n', encoding="utf-8")
    elif default_questions.exists():
        # Intentar fusionar las preguntas predeterminadas nuevas en el archivo del usuario
        merge_default_questions(default_questions, questions_path)

    return data_root

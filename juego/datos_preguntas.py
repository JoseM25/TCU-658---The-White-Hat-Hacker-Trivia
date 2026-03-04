import json
from collections.abc import Mapping
from pathlib import Path


def normalize_questions(raw_data):
    if isinstance(raw_data, Mapping):
        raw_questions = raw_data.get("questions", [])
    elif isinstance(raw_data, list):
        raw_questions = raw_data
    else:
        return []

    normalized = []
    for item in raw_questions:
        if not isinstance(item, Mapping):
            continue

        title = str(item.get("title", "") or "").strip()
        if not title:
            continue

        definition = str(item.get("definition", "") or "").strip()
        image = str(item.get("image", "") or "").strip()
        normalized.append(
            {
                "title": title,
                "definition": definition,
                "image": image,
            }
        )

    return normalized


def load_questions_file(path):
    path = Path(path)
    try:
        with open(path, "r", encoding="utf-8") as file:
            raw_data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []

    return normalize_questions(raw_data)

import json
from collections.abc import Mapping
from pathlib import Path
from tkinter import messagebox


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

    except FileNotFoundError:
        # Comportamiento esperado en la primera ejecución o si el archivo falta antes de crearse
        return []

    except json.JSONDecodeError as e:
        # Crítico: El archivo existe pero está corrupto.
        # Dejar que falle en silencio confunde a los usuarios que ven "Sin Preguntas".
        title = "Data Corruption Error"
        msg = (
            f"The questions file is corrupted and cannot be read.\n"
            f"Path: {path}\n\n"
            f"Error details: {str(e)}\n\n"
            f"The application will start with no questions."
        )
        messagebox.showerror(title, msg)
        return []

    except OSError as e:
        # Crítico: Error de permisos u otro fallo de lectura a nivel del sistema operativo.
        title = "File Read Error"
        msg = (
            f"Could not read the questions file due to a system error.\n"
            f"Path: {path}\n\n"
            f"Error details: {str(e)}"
        )
        messagebox.showerror(title, msg)
        return []

    return normalize_questions(raw_data)

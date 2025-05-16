# util_json.py
import json, os
from typing import Any

def load_json_safe(path: str, default: Any = None) -> Any:
    """
    Пробует прочитать JSON-файл.
    • Если файла нет, пустой он, битый или в нём не JSON — возвращает default.
    • default по умолчанию {}  (чтобы можно было сразу обращаться как к словарю).
    """
    if default is None:
        default = {}
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return default


def dump_json_safe(obj: Any, path: str) -> bool:
    """
    Записывает obj в JSON.  Возвращает True, если удалось сохранить, иначе False.
    Ошибка гасится, чтобы приложение не падало при проблемах с диском.
    """
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=4, ensure_ascii=False)
        return True
    except OSError:
        return False

"""Хранение опубликованных прокси и вычисление изменений."""
import json
from pathlib import Path

from .proxy_source import Proxy


def load_state(path: str) -> dict[str, dict]:
    """Загружает состояние: {key: {server, port, secret, message_id}}."""
    file = Path(path)
    if not file.exists():
        return {}
    return json.loads(file.read_text(encoding="utf-8"))


def save_state(path: str, state: dict[str, dict]) -> None:
    Path(path).write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def diff(current_keys: set[str], working: list[Proxy]) -> tuple[list[Proxy], set[str]]:
    """Возвращает (новые_для_добавления, ключи_для_удаления).

    - to_add: рабочие прокси, которых ещё нет в состоянии;
    - to_remove: ключи из состояния, которых больше нет среди рабочих.
    """
    working_keys = {p.key for p in working}
    to_add = [p for p in working if p.key not in current_keys]
    to_remove = current_keys - working_keys
    return to_add, to_remove
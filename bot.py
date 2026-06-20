"""Публикация рабочих прокси в чат через Telegram Bot API."""
import asyncio
import json
import os

import aiohttp

from config import (
    BOT_TOKEN, CHAT_ID, PROXY_SOURCE_URL,
    MAX_PROXIES, CHECK_INTERVAL_HOURS, STATE_FILE,
)
from checker import get_working_proxies

API = f"https://api.telegram.org/bot{BOT_TOKEN}"


async def api_call(session: aiohttp.ClientSession, method: str, **params):
    """Вызов метода Bot API."""
    async with session.post(f"{API}/{method}", json=params) as resp:
        data = await resp.json()
        if not data.get("ok"):
            raise RuntimeError(f"{method} failed: {data}")
        return data["result"]


def load_state() -> dict:
    """Загружает соответствие прокси -> id сообщения."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(state: dict) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


async def sync_proxies() -> None:
    """Синхронизирует чат с актуальным списком рабочих прокси."""
    state = load_state()                       # {key: message_id}
    proxies = await get_working_proxies(PROXY_SOURCE_URL, MAX_PROXIES)
    current = {p.key: p for p in proxies}

    async with aiohttp.ClientSession() as session:
        # 1. Удаляем устаревшие/нерабочие.
        for key, msg_id in list(state.items()):
            if key not in current:
                try:
                    await api_call(session, "deleteMessage",
                                   chat_id=CHAT_ID, message_id=msg_id)
                except Exception:
                    pass  # сообщение могло быть удалено вручную
                del state[key]

        # 2. Публикуем новые с кнопкой «Подключиться».
        for key, p in current.items():
            if key not in state:
                msg = await api_call(
                    session, "sendMessage",
                    chat_id=CHAT_ID,
                    text=f"🆕 MTProto-прокси\n`{p.server}:{p.port}`",
                    parse_mode="Markdown",
                    disable_web_page_preview=True,
                    reply_markup={
                        "inline_keyboard": [[
                            {"text": "🔌 Подключиться", "url": p.link}
                        ]]
                    },
                )
                state[key] = msg["message_id"]

    save_state(state)
    print(f"Синхронизировано прокси: {len(current)}")


async def main() -> None:
    """Запускает проверку циклически раз в CHECK_INTERVAL_HOURS."""
    while True:
        try:
            await sync_proxies()
        except Exception as e:
            print(f"Ошибка синхронизации: {e}")
        await asyncio.sleep(CHECK_INTERVAL_HOURS * 3600)


if __name__ == "__main__":
    asyncio.run(main())
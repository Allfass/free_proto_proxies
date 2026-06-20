"""Загрузка конфигурации из переменных окружения."""
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()  # подхватываем .env при локальном запуске


@dataclass(frozen=True)
class Config:
    api_id: int
    api_hash: str
    user_session: str
    bot_token: str
    target_chat_id: int
    source_url: str
    state_file: str


def load_config() -> Config:
    return Config(
        api_id=int(os.environ["API_ID"]),
        api_hash=os.environ["API_HASH"],
        user_session=os.environ["USER_SESSION"],
        bot_token=os.environ["BOT_TOKEN"],
        target_chat_id=int(os.environ["TARGET_CHAT_ID"]),
        source_url=os.environ.get(
            "SOURCE_URL",
            "https://raw.githubusercontent.com/SoliSpirit/mtproto/master/all_proxies.txt",
        ),
        state_file=os.environ.get("STATE_FILE", "state.json"),
    )
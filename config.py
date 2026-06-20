"""Конфигурация берётся из переменных окружения (.env)."""
import os
from dotenv import load_dotenv

load_dotenv()

# Токен бота от @BotFather
BOT_TOKEN = os.environ["BOT_TOKEN"]
# ID чата/канала, куда публикуем прокси (бот должен быть админом)
CHAT_ID = os.environ["CHAT_ID"]

# Источник списка прокси
PROXY_SOURCE_URL = os.getenv(
    "PROXY_SOURCE_URL",
    "https://raw.githubusercontent.com/SoliSpirit/mtproto/master/all_proxies.txt",
)

# Сколько максимум прокси держать опубликованными
MAX_PROXIES = int(os.getenv("MAX_PROXIES", "10"))
# Период проверки в часах
CHECK_INTERVAL_HOURS = int(os.getenv("CHECK_INTERVAL_HOURS", "24"))
# Файл с состоянием (какой прокси = какое сообщение)
STATE_FILE = os.getenv("STATE_FILE", "state.json")
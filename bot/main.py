"""Точка входа: публикация прокси и ежесуточная проверка."""
import asyncio
import logging

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .config import load_config
from .proxy_checker import filter_working
from .proxy_source import fetch_proxies
from .storage import diff, load_state, save_state

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("mtproto-bot")


async def sync_proxies(bot: Bot, config) -> None:
    """Один цикл синхронизации: скачать → проверить → обновить чат."""
    log.info("Старт синхронизации прокси")

    proxies = await fetch_proxies(config.source_url)
    log.info("Скачано прокси: %d", len(proxies))

    working = await filter_working(config.api_id, config.api_hash, proxies)
    log.info("Рабочих без рекламы: %d", len(working))

    state = load_state(config.state_file)
    to_add, to_remove = diff(set(state), working)

    # Удаляем устаревшие/нерабочие
    for key in to_remove:
        message_id = state[key].get("message_id")
        if message_id:
            try:
                await bot.delete_message(config.target_chat_id, message_id)
            except Exception as e:
                log.warning("Не удалось удалить сообщение %s: %s", message_id, e)
        state.pop(key, None)

    # Публикуем новые
    for proxy in to_add:
        msg = await bot.send_message(
            config.target_chat_id,
            f"🟢 Рабочий MTProto-прокси:\n{proxy.link}",
            disable_web_page_preview=True,
        )
        state[proxy.key] = {
            "server": proxy.server,
            "port": proxy.port,
            "secret": proxy.secret,
            "message_id": msg.message_id,
        }

    save_state(config.state_file, state)
    log.info("Готово. Добавлено: %d, удалено: %d", len(to_add), len(to_remove))


async def main() -> None:
    config = load_config()
    bot = Bot(token=config.bot_token)

    # Сразу прогон при старте
    await sync_proxies(bot, config)

    # Ежесуточный запуск
    scheduler = AsyncIOScheduler()
    scheduler.add_job(sync_proxies, "interval", days=1, args=(bot, config))
    scheduler.start()

    log.info("Бот запущен, планировщик активен")
    try:
        await asyncio.Event().wait()  # держим процесс живым
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
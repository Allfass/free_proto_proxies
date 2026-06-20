"""Проверка MTProto-прокси: доступность и отсутствие рекламы."""
import asyncio

from telethon import TelegramClient
from telethon.connection import ConnectionTcpMTProxyRandomizedIntermediate
from telethon.sessions import StringSession
from telethon.tl.functions.help import GetPromoDataRequest
from telethon.tl.types.help import PromoData

from .proxy_source import Proxy


async def check_proxy(
    api_id: int,
    api_hash: str,
    proxy: Proxy,
    timeout: int = 15,
) -> bool:
    """Возвращает True, если прокси рабочий И без рекламы.

    Логика:
      1. Подключаемся к Telegram через прокси.
      2. Запрашиваем getPromoData — если прокси рекламный,
         Telegram вернёт спонсорский канал (поле proxy=True).
    """
    client = TelegramClient(
        StringSession(),  # пустая сессия: нам нужно только подключение
        api_id,
        api_hash,
        connection=ConnectionTcpMTProxyRandomizedIntermediate,
        proxy=(proxy.server, proxy.port, proxy.secret),
        timeout=timeout,
    )

    try:
        await asyncio.wait_for(client.connect(), timeout=timeout)
        if not client.is_connected():
            return False  # не удалось подключиться → нерабочий

        promo = await client(GetPromoDataRequest())
        has_ad = isinstance(promo, PromoData) and getattr(promo, "proxy", False)
        return not has_ad  # рабочий и без рекламы
    except Exception:
        return False  # любой сбой считаем «нерабочим»
    finally:
        await client.disconnect()


async def filter_working(
    api_id: int,
    api_hash: str,
    proxies: list[Proxy],
    concurrency: int = 10,
) -> list[Proxy]:
    """Параллельно проверяет список и возвращает только годные прокси."""
    semaphore = asyncio.Semaphore(concurrency)  # ограничиваем нагрузку

    async def worker(p: Proxy) -> Proxy | None:
        async with semaphore:
            return p if await check_proxy(api_id, api_hash, p) else None

    results = await asyncio.gather(*(worker(p) for p in proxies))
    return [p for p in results if p is not None]
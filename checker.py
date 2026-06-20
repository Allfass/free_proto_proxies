"""Загрузка, парсинг, фильтрация и проверка MTProto-прокси."""
import asyncio
import re
from dataclasses import dataclass

import aiohttp

# Из любой строки достаём server, port, secret (ссылка t.me/proxy или tg://proxy).
PROXY_RE = re.compile(
    r"server=(?P<server>[\w.\-]+)&port=(?P<port>\d+)&secret=(?P<secret>[0-9a-fA-F]+)"
)

# Ограничиваем число одновременных проверок, чтобы не «положить» хост.
CONCURRENCY = 50


@dataclass(frozen=True)
class Proxy:
    server: str
    port: int
    secret: str

    @property
    def link(self) -> str:
        """Готовая ссылка для подключения к прокси."""
        return (
            f"https://t.me/proxy?server={self.server}"
            f"&port={self.port}&secret={self.secret}"
        )

    @property
    def key(self) -> str:
        """Уникальный ключ прокси (для дедупликации и state.json)."""
        return f"{self.server}:{self.port}:{self.secret}"


def parse_proxies(text: str) -> list[Proxy]:
    """Парсит текст файла в список уникальных прокси."""
    proxies, seen = [], set()
    for m in PROXY_RE.finditer(text):
        p = Proxy(m["server"], int(m["port"]), m["secret"].lower())
        if p.key not in seen:
            seen.add(p.key)
            proxies.append(p)
    return proxies


def has_no_ads(proxy: Proxy) -> bool:
    """Отсев прокси с рекламными признаками (best-effort в рамках Bot API).

    Стандартные секреты MTProto:
      - 32 hex-символа            — обычный секрет;
      - 34 символа (префикс 'dd') — secret с защитой от DPI;
      - 'ee' + домен              — FakeTLS.
    Нестандартная длина обычно означает «тегированный» секрет, который
    часто привязан к рекламному каналу — такие прокси отбрасываем.
    """
    s = proxy.secret
    return len(s) in (32, 34) or s.startswith("ee")


async def fetch_text(url: str) -> str:
    """Скачивает текстовый файл со списком прокси."""
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url) as resp:
            resp.raise_for_status()
            return await resp.text()


async def is_alive(proxy: Proxy, sem: asyncio.Semaphore, timeout: int = 5) -> bool:
    """Проверяет доступность прокси простым TCP-подключением."""
    async with sem:
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(proxy.server, proxy.port), timeout
            )
            writer.close()
            await writer.wait_closed()
            return True
        except Exception:
            return False


async def get_working_proxies(url: str, limit: int) -> list[Proxy]:
    """Возвращает до `limit` живых прокси без рекламы."""
    text = await fetch_text(url)
    proxies = [p for p in parse_proxies(text) if has_no_ads(p)]

    sem = asyncio.Semaphore(CONCURRENCY)
    alive_flags = await asyncio.gather(*(is_alive(p, sem) for p in proxies))

    alive = [p for p, ok in zip(proxies, alive_flags) if ok]
    return alive[:limit]
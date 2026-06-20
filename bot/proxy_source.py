"""Загрузка и разбор списка MTProto-прокси."""
import re
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

import aiohttp


@dataclass(frozen=True)
class Proxy:
    server: str
    port: int
    secret: str

    @property
    def key(self) -> str:
        """Уникальный ключ прокси — используется для сравнения состояний."""
        return f"{self.server}:{self.port}:{self.secret}"

    @property
    def link(self) -> str:
        """Готовая ссылка для публикации в чате."""
        return (
            f"https://t.me/proxy?server={self.server}"
            f"&port={self.port}&secret={self.secret}"
        )


def parse_proxies(text: str) -> list[Proxy]:
    """Разбирает текст файла в список прокси.

    Поддерживаются строки вида:
      - https://t.me/proxy?server=...&port=...&secret=...
      - tg://proxy?server=...&port=...&secret=...
      - server:port:secret
    Дубликаты удаляются автоматически.
    """
    proxies: dict[str, Proxy] = {}

    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        proxy = _parse_line(line)
        if proxy:
            proxies[proxy.key] = proxy  # dict убирает дубли по ключу

    return list(proxies.values())


def _parse_line(line: str) -> Proxy | None:
    # Формат-ссылка (t.me / tg://)
    if "proxy?" in line:
        query = parse_qs(urlparse(line).query)
        try:
            return Proxy(
                server=query["server"][0],
                port=int(query["port"][0]),
                secret=query["secret"][0],
            )
        except (KeyError, ValueError, IndexError):
            return None

    # Формат server:port:secret
    if re.match(r"^[^:\s]+:\d+:[0-9a-fA-Fee]+$", line):
        server, port, secret = line.split(":", 2)
        return Proxy(server=server, port=int(port), secret=secret)

    return None


async def fetch_proxies(url: str, timeout: int = 30) -> list[Proxy]:
    """Скачивает файл и возвращает список прокси."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
            resp.raise_for_status()
            text = await resp.text()
    return parse_proxies(text)
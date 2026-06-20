from bot.proxy_source import parse_proxies, Proxy


def test_parse_link_format():
    text = "https://t.me/proxy?server=1.2.3.4&port=443&secret=abc123"
    proxies = parse_proxies(text)
    assert proxies == [Proxy("1.2.3.4", 443, "abc123")]


def test_parse_colon_format():
    proxies = parse_proxies("1.2.3.4:443:deadbeef")
    assert proxies[0].port == 443
    assert proxies[0].secret == "deadbeef"


def test_removes_duplicates_and_comments():
    text = (
        "# комментарий\n"
        "1.2.3.4:443:aaa\n"
        "https://t.me/proxy?server=1.2.3.4&port=443&secret=aaa\n"
        "\n"
    )
    assert len(parse_proxies(text)) == 1


def test_ignores_invalid_lines():
    assert parse_proxies("совсем не прокси") == []


def test_link_property():
    p = Proxy("host", 443, "xyz")
    assert p.link == "https://t.me/proxy?server=host&port=443&secret=xyz"
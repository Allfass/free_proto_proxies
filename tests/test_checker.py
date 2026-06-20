from checker import Proxy, parse_proxies, has_no_ads


def test_parse_basic():
    text = "https://t.me/proxy?server=1.2.3.4&port=443&secret=" + "a" * 32
    proxies = parse_proxies(text)
    assert len(proxies) == 1
    assert proxies[0].server == "1.2.3.4"
    assert proxies[0].port == 443


def test_parse_deduplicates():
    line = "server=1.2.3.4&port=443&secret=" + "a" * 32
    assert len(parse_proxies(line + "\n" + line)) == 1


def test_link_format():
    p = Proxy("1.2.3.4", 443, "a" * 32)
    assert p.link == (
        "https://t.me/proxy?server=1.2.3.4&port=443&secret=" + "a" * 32
    )


def test_has_no_ads_standard():
    assert has_no_ads(Proxy("h", 1, "a" * 32))        # обычный
    assert has_no_ads(Proxy("h", 1, "dd" + "a" * 32)) # анти-DPI
    assert has_no_ads(Proxy("h", 1, "ee" + "ab"))     # FakeTLS


def test_has_ads_nonstandard():
    assert not has_no_ads(Proxy("h", 1, "a" * 40))    # «тегированный»
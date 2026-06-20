import json
from bot.proxy_source import Proxy
from bot.storage import diff, load_state, save_state


def test_diff_add_and_remove():
    working = [Proxy("h1", 443, "s1")]
    current = {"old:443:x", "h1:443:s1"}
    to_add, to_remove = diff(current, working)
    assert to_add == []                 # h1 уже есть
    assert to_remove == {"old:443:x"}   # old больше не рабочий


def test_diff_new_proxy():
    working = [Proxy("new", 443, "s")]
    to_add, to_remove = diff(set(), working)
    assert to_add == working
    assert to_remove == set()


def test_state_roundtrip(tmp_path):
    path = tmp_path / "state.json"
    data = {"h:443:s": {"server": "h", "port": 443, "secret": "s", "message_id": 10}}
    save_state(str(path), data)
    assert load_state(str(path)) == data


def test_load_missing_file(tmp_path):
    assert load_state(str(tmp_path / "nope.json")) == {}
"""Tests for tracked_dict."""

import pytest
from tracked_dict import TrackedDict, TrackedList


# --- TrackedDict basics ---

class TestTrackedDictAccess:
    def test_getitem(self):
        d = TrackedDict({"a": 1, "b": 2})
        assert d["a"] == 1
        assert d["b"] == 2

    def test_getitem_missing_raises(self):
        d = TrackedDict({"a": 1})
        with pytest.raises(KeyError):
            d["z"]

    def test_get_present(self):
        d = TrackedDict({"a": 1})
        assert d.get("a") == 1

    def test_get_missing_default(self):
        d = TrackedDict({"a": 1})
        assert d.get("z") is None
        assert d.get("z", 42) == 42

    def test_contains(self):
        d = TrackedDict({"a": 1})
        assert "a" in d
        assert "z" not in d

    def test_len(self):
        assert len(TrackedDict({})) == 0
        assert len(TrackedDict({"a": 1, "b": 2})) == 2

    def test_bool(self):
        assert not TrackedDict({})
        assert TrackedDict({"a": 1})

    def test_iter(self):
        d = TrackedDict({"a": 1, "b": 2})
        assert set(d) == {"a", "b"}

    def test_keys(self):
        d = TrackedDict({"x": 10, "y": 20})
        assert set(d.keys()) == {"x", "y"}

    def test_values(self):
        d = TrackedDict({"x": 10, "y": 20})
        assert list(d.values()) == [10, 20]

    def test_items(self):
        d = TrackedDict({"x": 10, "y": 20})
        assert list(d.items()) == [("x", 10), ("y", 20)]

    def test_raw(self):
        original = {"a": 1}
        d = TrackedDict(original)
        assert d.raw is original

    def test_repr(self):
        d = TrackedDict({"a": 1, "b": 2})
        d["a"]
        r = repr(d)
        assert "1/2" in r
        assert "TrackedDict" in r

    def test_eq_dict(self):
        d = TrackedDict({"a": 1})
        assert d == {"a": 1}
        assert d != {"a": 2}

    def test_eq_tracked(self):
        d1 = TrackedDict({"a": 1})
        d2 = TrackedDict({"a": 1})
        assert d1 == d2


# --- Tracking ---

class TestTrackedDictTracking:
    def test_unaccessed_all(self):
        d = TrackedDict({"a": 1, "b": 2, "c": 3})
        assert d.unaccessed() == ["a", "b", "c"]

    def test_unaccessed_partial(self):
        d = TrackedDict({"a": 1, "b": 2, "c": 3})
        d["b"]
        assert d.unaccessed() == ["a", "c"]

    def test_unaccessed_none(self):
        d = TrackedDict({"a": 1, "b": 2})
        d["a"]
        d["b"]
        assert d.unaccessed() == []

    def test_get_marks_accessed(self):
        d = TrackedDict({"a": 1, "b": 2})
        d.get("a")
        assert d.unaccessed() == ["b"]

    def test_get_missing_marks_accessed(self):
        """get() for missing key still marks it, preventing false positives on re-check."""
        d = TrackedDict({"a": 1})
        d.get("z")
        assert d.unaccessed() == ["a"]

    def test_contains_does_not_mark(self):
        d = TrackedDict({"a": 1})
        _ = "a" in d
        assert d.unaccessed() == ["a"]

    def test_iter_does_not_mark(self):
        d = TrackedDict({"a": 1})
        list(d)
        assert d.unaccessed() == ["a"]

    def test_keys_does_not_mark(self):
        d = TrackedDict({"a": 1})
        list(d.keys())
        assert d.unaccessed() == ["a"]

    def test_values_marks_all(self):
        d = TrackedDict({"a": 1, "b": 2})
        list(d.values())
        assert d.unaccessed() == []

    def test_items_marks_all(self):
        d = TrackedDict({"a": 1, "b": 2})
        list(d.items())
        assert d.unaccessed() == []

    def test_mark_accessed(self):
        d = TrackedDict({"a": 1, "b": 2, "c": 3})
        d.mark_accessed("a", "c")
        assert d.unaccessed() == ["b"]

    def test_mark_all_accessed(self):
        d = TrackedDict({"a": 1, "b": 2})
        d.mark_all_accessed()
        assert d.unaccessed() == []

    def test_accessed_keys(self):
        d = TrackedDict({"a": 1, "b": 2, "c": 3})
        d["a"]
        d.get("c")
        assert d.accessed_keys() == {"a", "c"}


# --- Nested structures ---

class TestNestedTracking:
    def test_nested_dict_wrapped(self):
        d = TrackedDict({"outer": {"inner": 1}})
        inner = d["outer"]
        assert isinstance(inner, TrackedDict)
        assert inner["inner"] == 1

    def test_nested_dict_unaccessed(self):
        d = TrackedDict({"outer": {"a": 1, "b": 2}})
        d["outer"]["a"]
        assert d.unaccessed() == ["outer.b"]

    def test_deeply_nested(self):
        d = TrackedDict({"l1": {"l2": {"l3": {"val": 42}}}})
        assert d["l1"]["l2"]["l3"]["val"] == 42
        assert d.unaccessed() == []

    def test_deeply_nested_partial(self):
        d = TrackedDict({"l1": {"l2": {"a": 1, "b": 2}, "c": 3}})
        d["l1"]["l2"]["a"]
        assert d.unaccessed() == ["l1.c", "l1.l2.b"]

    def test_nested_list_of_dicts(self):
        d = TrackedDict({"items": [{"x": 1, "y": 2}, {"x": 3, "y": 4}]})
        items = d["items"]
        assert isinstance(items, TrackedList)
        assert items[0]["x"] == 1
        assert items[1]["x"] == 3
        assert d.unaccessed() == ["items[0].y", "items[1].y"]

    def test_nested_wrapping_is_stable(self):
        """Same child returned on repeated access."""
        d = TrackedDict({"sub": {"a": 1}})
        c1 = d["sub"]
        c2 = d["sub"]
        assert c1 is c2

    def test_nested_list_wrapping_is_stable(self):
        d = TrackedDict({"arr": [{"a": 1}]})
        lst = d["arr"]
        c1 = lst[0]
        c2 = lst[0]
        assert c1 is c2

    def test_path_formatting(self):
        d = TrackedDict({"a": {"b": [{"c": 1, "d": 2}]}})
        d["a"]["b"][0]["c"]
        unaccessed = d.unaccessed()
        assert "a.b[0].d" in unaccessed

    def test_mark_accessed_skips_nested_report(self):
        """Marking a parent key accessed suppresses nested reporting."""
        d = TrackedDict({"section": {"a": 1, "b": 2}})
        d.mark_accessed("section")
        assert d.unaccessed() == []


# --- TrackedList ---

class TestTrackedList:
    def test_getitem_scalar(self):
        lst = TrackedList([10, 20, 30])
        assert lst[0] == 10
        assert lst[2] == 30

    def test_len(self):
        assert len(TrackedList([])) == 0
        assert len(TrackedList([1, 2])) == 2

    def test_bool(self):
        assert not TrackedList([])
        assert TrackedList([1])

    def test_iter(self):
        lst = TrackedList([1, 2, 3])
        assert list(lst) == [1, 2, 3]

    def test_raw(self):
        original = [1, 2]
        lst = TrackedList(original)
        assert lst.raw is original

    def test_repr(self):
        r = repr(TrackedList([1, 2, 3]))
        assert "3 items" in r

    def test_eq_list(self):
        assert TrackedList([1, 2]) == [1, 2]
        assert TrackedList([1, 2]) != [3]

    def test_nested_dict_in_list(self):
        lst = TrackedList([{"a": 1, "b": 2}])
        item = lst[0]
        assert isinstance(item, TrackedDict)
        item["a"]
        assert lst.unaccessed() == ["[0].b"]

    def test_nested_list_in_list(self):
        lst = TrackedList([[{"x": 1}]])
        inner = lst[0]
        assert isinstance(inner, TrackedList)
        inner[0]["x"]
        assert lst.unaccessed() == []

    def test_scalars_no_unaccessed(self):
        lst = TrackedList([1, "two", 3.0])
        list(lst)
        assert lst.unaccessed() == []


# --- Real-world pattern: JSON config ---

class TestRealWorldPattern:
    def test_json_config_pattern(self):
        config = {
            "server": {
                "host": "localhost",
                "port": 8080,
                "debug": True,
                "timeout": 30,
            },
            "database": {
                "url": "sqlite:///db.sqlite",
                "pool_size": 5,
            },
        }
        d = TrackedDict(config)

        # Parser reads what it needs
        host = d["server"]["host"]
        port = d["server"]["port"]
        db_url = d["database"]["url"]

        assert host == "localhost"
        assert port == 8080
        assert db_url == "sqlite:///db.sqlite"

        unused = d.unaccessed()
        assert "server.debug" in unused
        assert "server.timeout" in unused
        assert "database.pool_size" in unused
        assert len(unused) == 3

    def test_bulk_forward_pattern(self):
        """Sections forwarded to another subsystem can be marked wholesale."""
        config = {
            "app": {"name": "test"},
            "logging": {"level": "debug", "file": "/var/log/app.log"},
        }
        d = TrackedDict(config)
        d["app"]["name"]
        d.mark_accessed("logging")  # forwarded to logging subsystem
        assert d.unaccessed() == []

    def test_list_of_items_pattern(self):
        config = {
            "plugins": [
                {"name": "auth", "enabled": True, "config": {}},
                {"name": "cache", "enabled": False, "config": {}},
            ]
        }
        d = TrackedDict(config)
        for plugin in d["plugins"]:
            _ = plugin["name"]
            _ = plugin["enabled"]

        unused = d.unaccessed()
        assert unused == ["plugins[0].config", "plugins[1].config"]

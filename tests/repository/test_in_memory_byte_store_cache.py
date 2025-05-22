import pytest

from apexdevkit.repository import InMemoryByteStore


def test_should_cache_store() -> None:
    cache = InMemoryByteStore.Cache()
    store = cache.store_for("name")

    store.set("key", b"value")

    assert cache.store_for("name").get("key") == b"value"


def test_should_clear_cache() -> None:
    cache = InMemoryByteStore.Cache()
    store = cache.store_for("name")
    store.set("key", b"value")

    cache.clear()

    with pytest.raises(KeyError, match="key"):
        cache.store_for("name").get("key")

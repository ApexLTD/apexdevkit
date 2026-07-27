from dataclasses import replace

from apexdevkit.repository import BruteForceBatch, InMemoryRepository
from tests.repository.data import AppleItem


def test_should_load_missing() -> None:
    target = [AppleItem(color="red")]
    new = [
        AppleItem(color="green"),
        AppleItem(color="blue"),
    ]
    storage = InMemoryRepository[AppleItem]().with_seeded(*target)
    batch = BruteForceBatch(inner=storage)

    loaded = batch.load(source=new)

    assert list(loaded) == [replace(apple) for apple in new]
    assert list(batch) == [replace(apple) for apple in target + new]


def test_should_not_load_existing() -> None:
    target = [AppleItem(color="red")]
    new = [
        AppleItem(color="green"),
        AppleItem(color="blue"),
    ]
    storage = InMemoryRepository[AppleItem]().with_seeded(*target)
    batch = BruteForceBatch(inner=storage)

    loaded = batch.load(source=target + new)

    assert list(loaded) == [replace(apple) for apple in new]
    assert list(batch) == [replace(apple) for apple in target + new]


def test_should_prune_existing() -> None:
    current = [
        AppleItem(color="red"),
        AppleItem(color="green"),
        AppleItem(color="blue"),
    ]
    *remaining, removed = current

    batch = BruteForceBatch(inner=InMemoryRepository[AppleItem]().with_seeded(*current))

    pruned = batch.prune(source=[removed])

    assert list(pruned) == [replace(removed)]
    assert list(batch) == [replace(apple) for apple in remaining]


def test_should_not_prune_missing() -> None:
    current = [AppleItem(color="green"), AppleItem(color="blue")]
    missing = [AppleItem(color="red")]
    batch = BruteForceBatch(inner=InMemoryRepository[AppleItem]().with_seeded(*current))

    pruned = batch.prune(source=missing)

    assert list(pruned) == []
    assert list(batch) == [replace(apple) for apple in current]

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
    missing = [AppleItem(color="red")]
    source = [AppleItem(color="green"), AppleItem(color="blue")]
    batch = BruteForceBatch(
        inner=InMemoryRepository[AppleItem]().with_seeded(*source, *missing)
    )

    pruned = batch.prune(source=source)

    assert list(pruned) == [replace(apple) for apple in missing]
    assert list(batch) == [replace(apple) for apple in source]


def test_should_not_prune_missing() -> None:
    source = [AppleItem(color="green"), AppleItem(color="blue")]
    batch = BruteForceBatch(inner=InMemoryRepository[AppleItem]().with_seeded(*source))

    pruned = batch.prune(source=source)

    assert list(pruned) == []
    assert list(batch) == [replace(apple) for apple in source]

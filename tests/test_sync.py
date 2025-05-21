from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from uuid import uuid4

from apexdevkit.synchronization import FullSync, Sync


@dataclass
class Apple:
    color: str

    id: str = field(default_factory=lambda: str(uuid4()))


@dataclass
class FakeSource:
    returns: list[Apple] = field(default_factory=list)
    input: list[Apple] = field(default_factory=list)

    def value_of(self, items: Iterable[Apple]) -> Iterable[Apple]:
        self.input = list(items)
        yield from self.returns


@dataclass
class FakeTarget:
    imported: list[Apple] = field(default_factory=list)
    updates: list[Apple] = field(default_factory=list)

    def __iter__(self) -> Iterator[Apple]:
        yield from self.imported

    def update_many(self, items: Iterable[Apple]) -> None:
        self.updates = list(items)


def test_should_synchronize() -> None:
    imported = [Apple("RED")]
    returned = [Apple("GREEN")]

    source = FakeSource(returns=returned)
    target = FakeTarget(imported=imported)

    Sync[Apple](source, target).sync()

    assert source.input == imported
    assert target.updates == returned


def test_should_synchronize_full() -> None:
    source = [Apple("RED")]

    target = FakeTarget()

    FullSync[Apple](source, target).sync()

    assert target.updates == source

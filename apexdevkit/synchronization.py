from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Iterable, Iterator, Protocol, TypeVar

ItemT = TypeVar("ItemT")


@dataclass(frozen=True)
class Sync(Generic[ItemT]):
    source: _Source[ItemT]
    target: _Target[ItemT]

    def sync(self) -> None:
        items = self.source.value_of(list(self.target))
        self.target.update_many(list(items))


class _Source(Protocol[ItemT]):
    def value_of(self, items: Iterable[ItemT]) -> Iterable[ItemT]:
        pass


class _Target(Protocol[ItemT]):
    def __iter__(self) -> Iterator[ItemT]:
        pass

    def update_many(self, items: Iterable[ItemT]) -> None:
        pass

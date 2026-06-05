from __future__ import annotations

from collections.abc import Callable, Collection, Container, Iterable
from dataclasses import dataclass, field
from typing import Protocol, TypeVar
from uuid import uuid4


def _uuid() -> str:
    return str(uuid4())


@dataclass(frozen=True, kw_only=True)
class Entity:
    id: str = field(default_factory=_uuid)
    idempotency_id: str | None = field(default=None)


ItemT = TypeVar("ItemT", bound=Entity)
KeyFn = Callable[[ItemT], str]


class Repository(Collection[ItemT], Protocol[ItemT]):  # pragma: no cover
    def create(self, item: ItemT) -> ItemT:
        pass

    def read(self, item_id: str) -> ItemT:
        pass

    def update(self, item: ItemT) -> None:
        pass

    def delete(self, item_id: str) -> None:
        pass


class BatchRepository(Repository[ItemT], Protocol[ItemT]):  # pragma: no cover
    def load(self, source: Iterable[ItemT]) -> Iterable[ItemT]:
        pass

    def prune(self, source: Container[ItemT]) -> Iterable[ItemT]:
        pass

    def renew(self, source: Iterable[ItemT]) -> Iterable[ItemT]:
        pass

from __future__ import annotations

from collections.abc import Callable, Collection, Iterable, Iterator
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
    def create_many(self, items: Iterable[ItemT]) -> Iterable[ItemT]:
        pass

    def update_many(self, items: Iterable[ItemT]) -> None:
        pass


class RepositoryBase(Repository[ItemT]):  # pragma: no cover
    def create(self, item: ItemT) -> ItemT:
        raise NotImplementedError

    def read(self, item_id: str) -> ItemT:
        raise NotImplementedError

    def update(self, item: ItemT) -> None:
        raise NotImplementedError

    def delete(self, item_id: str) -> None:
        raise NotImplementedError

    def __iter__(self) -> Iterator[ItemT]:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError

    def __contains__(self, item: object) -> bool:
        raise NotImplementedError

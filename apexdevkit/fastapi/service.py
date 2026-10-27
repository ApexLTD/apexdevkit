from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol

from pypebbles import JsonDict

from apexdevkit.repository import Entity, Repository

if TYPE_CHECKING:
    from apexdevkit.formatter import Formatter

RawItem = Mapping[str, Any]
RawCollection = Iterable[RawItem]


class NoFormatter[T]:
    def load(self, source: RawItem) -> T:
        raise NotImplementedError

    def dump(self, target: T) -> RawItem:
        raise NotImplementedError


class NoService[T: Entity]:
    def create_one(self, item: T) -> T:
        raise NotImplementedError

    def read_one(self, *, with_id: str) -> T:
        raise NotImplementedError

    def read_all(self) -> Iterable[T]:
        raise NotImplementedError

    def read_many(self, query: JsonDict) -> Iterable[T]:
        raise NotImplementedError

    def update_one(self, item: T) -> T:
        raise NotImplementedError

    def delete_one(self, with_id: str) -> T:
        raise NotImplementedError


@dataclass(frozen=True, kw_only=True)
class RestfulService[T: Entity]:
    inner: _Service[T] = field(default_factory=NoService)
    formatter: Formatter[RawItem, T] = field(default_factory=NoFormatter)

    def create_one(self, item: RawItem) -> RawItem:
        result = self.inner.create_one(self.formatter.load(item))

        return self.formatter.dump(result)

    def read_one(self, item_id: str) -> RawItem:
        result = self.inner.read_one(with_id=item_id)

        return self.formatter.dump(result)

    def read_all(self) -> RawCollection:
        result = self.inner.read_all()

        return [self.formatter.dump(item) for item in result]

    def read_many(self, **params: Any) -> RawCollection:
        result = self.inner.read_many(JsonDict(params))

        return [self.formatter.dump(item) for item in result]

    def update_one(self, item_id: str, **with_fields: Any) -> RawItem:
        current = self.inner.read_one(with_id=item_id)
        updated = {**self.formatter.dump(current), **with_fields}
        result = self.inner.update_one(self.formatter.load(updated))

        return self.formatter.dump(result)

    def replace_one(self, item: RawItem) -> RawItem:
        result = self.inner.update_one(self.formatter.load(item))

        return self.formatter.dump(result)

    def delete_one(self, item_id: str) -> None:
        self.inner.delete_one(with_id=item_id)


class _Service[T: Entity](Protocol):
    def create_one(self, item: T) -> T:
        pass

    def read_one(self, *, with_id: str) -> T:
        pass

    def read_all(self) -> Iterable[T]:
        pass

    def read_many(self, query: JsonDict) -> Iterable[T]:
        pass

    def update_one(self, item: T) -> T:
        pass

    def delete_one(self, with_id: str) -> T:
        pass


@dataclass(frozen=True)
class RepositoryBasedService[T: Entity](_Service[T]):
    repository: Repository[T]

    def create_one(self, item: T) -> T:
        return self.repository.create(item)

    def read_one(self, *, with_id: str) -> T:
        return self.repository.read(with_id)

    def read_all(self) -> Iterable[T]:
        yield from self.repository

    def read_many(self, query: JsonDict) -> Iterable[T]:
        raise NotImplementedError

    def update_one(self, item: T) -> T:
        self.repository.update(item)

        return item

    def delete_one(self, with_id: str) -> T:
        result = self.repository.read(with_id)

        self.repository.delete(with_id)

        return result

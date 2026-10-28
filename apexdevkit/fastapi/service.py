from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol

from pypebbles import JsonDict

from apexdevkit.formatter import NoFormatter

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from apexdevkit.formatter import Formatter
    from apexdevkit.repository import Entity, Repository


class NoService[T]:
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
class RestfulResource[T]:
    service: RestfulService[T] = field(default_factory=NoService)
    formatter: Formatter[Mapping[str, Any], T] = field(default_factory=NoFormatter)

    def create_one(self, item: Mapping[str, Any]) -> Mapping[str, Any]:
        result = self.service.create_one(self.formatter.load(item))

        return self.formatter.dump(result)

    def read_one(self, item_id: str) -> Mapping[str, Any]:
        result = self.service.read_one(with_id=item_id)

        return self.formatter.dump(result)

    def read_all(self) -> Iterable[Mapping[str, Any]]:
        result = self.service.read_all()

        return [self.formatter.dump(item) for item in result]

    def read_many(self, **params: Any) -> Iterable[Mapping[str, Any]]:
        result = self.service.read_many(JsonDict(params))

        return [self.formatter.dump(item) for item in result]

    def update_one(self, item_id: str, **with_fields: Any) -> Mapping[str, Any]:
        current = self.service.read_one(with_id=item_id)
        updated = {**self.formatter.dump(current), **with_fields}
        result = self.service.update_one(self.formatter.load(updated))

        return self.formatter.dump(result)

    def replace_one(self, item: Mapping[str, Any]) -> Mapping[str, Any]:
        result = self.service.update_one(self.formatter.load(item))

        return self.formatter.dump(result)

    def delete_one(self, item_id: str) -> None:
        self.service.delete_one(with_id=item_id)


class RestfulService[T](Protocol):
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
class RestfulRepository[T: Entity](RestfulService[T]):
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

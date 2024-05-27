from abc import ABC
from dataclasses import asdict, dataclass, replace
from typing import Any, Iterable

from apexdevkit.repository import InMemoryRepository

_RawItem = dict[str, Any]
_RawCollection = Iterable[_RawItem]


class RestfulService(ABC):
    def create_one(self, item: _RawItem) -> _RawItem:
        raise NotImplementedError(self.create_one.__name__)

    def create_many(self, items: _RawCollection) -> _RawCollection:
        raise NotImplementedError(self.create_many.__name__)

    def read_one(self, item_id: str) -> _RawItem:
        raise NotImplementedError(self.read_one.__name__)

    def read_all(self) -> _RawCollection:
        raise NotImplementedError(self.read_all.__name__)

    def update_one(self, item_id: str, **with_fields: Any) -> _RawItem:
        raise NotImplementedError(self.update_one.__name__)

    def update_many(self, items: _RawCollection) -> _RawCollection:
        raise NotImplementedError(self.update_many.__name__)

    def delete_one(self, item_id: str) -> None:
        raise NotImplementedError(self.delete_one.__name__)


def _as_raw_collection(value: Iterable[Any]) -> _RawCollection:
    return [_as_raw_item(item) for item in value]


def _as_raw_item(value: Any) -> _RawItem:
    return asdict(value)


@dataclass
class InMemoryRestfulService(RestfulService):
    resource: type[Any]
    repository: InMemoryRepository[Any]

    def create_one(self, item: _RawItem) -> _RawItem:
        result = self.resource(**item)

        self.repository.create(result)

        return _as_raw_item(result)

    def create_many(self, items: _RawCollection) -> _RawCollection:
        result = [self.resource(**fields) for fields in items]

        self.repository.create_many(result)

        return _as_raw_collection(result)

    def read_one(self, item_id: str) -> _RawItem:
        result = self.repository.read(item_id)

        return _as_raw_item(result)

    def read_all(self) -> _RawCollection:
        result = self.repository

        return _as_raw_collection(result)

    def update_one(self, item_id: str, **with_fields: Any) -> _RawItem:
        result = replace(self.repository.read(item_id), **with_fields)

        self.repository.update(result)

        return _as_raw_item(result)

    def update_many(self, items: _RawCollection) -> _RawCollection:
        result = [self.resource(**fields) for fields in items]

        self.repository.update_many(result)

        return _as_raw_collection(result)

    def delete_one(self, item_id: str) -> None:
        self.repository.delete(item_id)

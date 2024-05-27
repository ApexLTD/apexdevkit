from dataclasses import asdict, dataclass, replace
from typing import Any, Iterable, Protocol

from apexdevkit.repository import InMemoryRepository

_RawItem = dict[str, Any]
_RawCollection = Iterable[_RawItem]


class RestfulService(Protocol):
    def create_one(self, item: _RawItem) -> _RawItem:
        pass

    def create_many(self, items: _RawCollection) -> _RawCollection:
        pass

    def read_one(self, item_id: str) -> _RawItem:
        pass

    def read_all(self) -> _RawCollection:
        pass

    def update_one(self, item_id: str, **with_fields: Any) -> _RawItem:
        pass

    def update_many(self, items: _RawCollection) -> _RawCollection:
        pass

    def delete_one(self, item_id: str) -> None:
        pass


def _as_raw_collection(value: Iterable[Any]) -> _RawCollection:
    return [_as_raw_item(item) for item in value]


def _as_raw_item(value: Any) -> _RawItem:
    return asdict(value)


@dataclass
class InMemoryRestfulService:
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

from abc import ABC
from dataclasses import asdict, dataclass, replace
from typing import Any, Iterable

from apexdevkit.repository.interface import Repository

RawItem = dict[str, Any]
RawCollection = Iterable[RawItem]


class RestfulService(ABC):
    def create_one(self, item: RawItem) -> RawItem:
        raise NotImplementedError(self.create_one.__name__)

    def create_many(self, items: RawCollection) -> RawCollection:
        raise NotImplementedError(self.create_many.__name__)

    def read_one(self, item_id: str) -> RawItem:
        raise NotImplementedError(self.read_one.__name__)

    def read_all(self) -> RawCollection:
        raise NotImplementedError(self.read_all.__name__)

    def update_one(self, item_id: str, **with_fields: Any) -> RawItem:
        raise NotImplementedError(self.update_one.__name__)

    def update_many(self, items: RawCollection) -> RawCollection:
        raise NotImplementedError(self.update_many.__name__)

    def delete_one(self, item_id: str) -> None:
        raise NotImplementedError(self.delete_one.__name__)


def _as_raw_collection(value: Iterable[Any]) -> RawCollection:
    return [_as_raw_item(item) for item in value]


def _as_raw_item(value: Any) -> RawItem:
    return asdict(value)


@dataclass
class RestfulRepository(RestfulService):
    resource: type[Any]
    repository: Repository[Any, Any]

    def create_one(self, item: RawItem) -> RawItem:
        result = self.resource(**item)

        self.repository.create(result)

        return _as_raw_item(result)

    def create_many(self, items: RawCollection) -> RawCollection:
        result = [self.resource(**fields) for fields in items]

        self.repository.create_many(result)

        return _as_raw_collection(result)

    def read_one(self, item_id: str) -> RawItem:
        result = self.repository.read(item_id)

        return _as_raw_item(result)

    def read_all(self) -> RawCollection:
        result = self.repository

        return _as_raw_collection(result)

    def update_one(self, item_id: str, **with_fields: Any) -> RawItem:
        result = replace(self.repository.read(item_id), **with_fields)

        self.repository.update(result)

        return _as_raw_item(result)

    def update_many(self, items: RawCollection) -> RawCollection:
        result = [self.resource(**fields) for fields in items]

        self.repository.update_many(result)

        return _as_raw_collection(result)

    def delete_one(self, item_id: str) -> None:
        self.repository.delete(item_id)

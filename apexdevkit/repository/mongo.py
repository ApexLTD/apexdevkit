from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ContextManager, Dict, Generic, Iterator, Protocol, TypeVar

from pymongo import MongoClient, ReturnDocument
from pymongo.collection import Collection
from pymongo.results import DeleteResult, InsertOneResult

from apexdevkit.error import DoesNotExistError, ExistsError
from apexdevkit.formatter import Formatter


class _Item(Protocol):  # pragma: no cover
    @property
    def id(self) -> Any:
        pass


ItemT = TypeVar("ItemT", bound=_Item)


@dataclass
class MongoDBRepository(Generic[ItemT]):
    database: MongoDatabase
    formatter: Formatter[dict[str, Any], ItemT]

    def __iter__(self) -> Iterator[ItemT]:
        for raw in self.database:
            yield self.formatter.load(raw)

    def __len__(self) -> int:
        return len(self.database)

    def create(self, item: ItemT) -> ItemT:
        try:
            self.read(item.id)
            raise ExistsError(item).with_duplicate(
                lambda i: f"_Item with id<{i.id}> already exists."
            )
        except DoesNotExistError:
            self.database.create(self.formatter.dump(item))
            return item

    def create_many(self, items: list[ItemT]) -> list[ItemT]:
        return [self.create(item) for item in items]

    def read(self, item_id: str) -> ItemT:
        raw = self.database.read(item_id)

        if not raw:
            raise DoesNotExistError(item_id)

        return self.formatter.load(raw)

    def update(self, item: ItemT) -> None:
        self.database.update(item.id, self.formatter.dump(item))

    def update_many(self, items: list[ItemT]) -> None:
        for item in items:
            self.update(item)

    def delete(self, item_id: str) -> None:
        result = self.database.delete(item_id)
        if result.deleted_count == 0:
            raise DoesNotExistError(item_id)


@dataclass
class MongoDatabase:
    connector: MongoConnector
    database_name: str
    collection_name: str

    def collection(self, client: MongoClient[Any]) -> Collection[Any]:
        return client[self.database_name][self.collection_name]

    def __iter__(self) -> Iterator[Any]:
        with self.connector.connect() as client:
            for raw in self.collection(client).find():
                yield raw

    def __len__(self) -> int:
        with self.connector.connect() as client:
            return self.collection(client).count_documents({})

    def create(self, item: Dict[str, Any]) -> InsertOneResult:
        with self.connector.connect() as client:
            return self.collection(client).insert_one(item)

    def read(self, item_id: str) -> Dict[str, Any] | None:
        with self.connector.connect() as client:
            return self.collection(client).find_one({"id": item_id})

    def update(self, item_id: str, item: Dict[str, Any]) -> Any:
        with self.connector.connect() as client:
            return self.collection(client).find_one_and_update(
                {"id": item_id},
                {"$set": item},
                return_document=ReturnDocument.AFTER,
            )

    def delete(self, item_id: str) -> DeleteResult:
        with self.connector.connect() as client:
            return self.collection(client).delete_one({"id": item_id})


class MongoConnector(Protocol):  # pragma: no cover
    def connect(self) -> ContextManager[MongoClient[Any]]:
        pass

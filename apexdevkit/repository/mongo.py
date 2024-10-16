from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ContextManager, Generic, Iterator, Protocol, TypeVar

from pymongo import MongoClient, ReturnDocument
from pymongo.collection import Collection

from apexdevkit.error import DoesNotExistError, ExistsError
from apexdevkit.formatter import Formatter


class _Item(Protocol):  # pragma: no cover
    @property
    def id(self) -> Any:
        pass


ItemT = TypeVar("ItemT", bound=_Item)


@dataclass(frozen=True)
class MongoRepository(Generic[ItemT]):
    connector: MongoConnector
    database_name: str
    collection_name: str
    formatter: Formatter[dict[str, Any], ItemT]

    def collection(self, client: MongoClient[Any]) -> Collection[Any]:
        return client[self.database_name][self.collection_name]

    def __iter__(self) -> Iterator[ItemT]:
        with self.connector.connect() as client:
            for raw in self.collection(client).find():
                yield self.formatter.load(raw)

    def __len__(self) -> int:
        with self.connector.connect() as client:
            return self.collection(client).count_documents({})

    def create(self, item: ItemT) -> ItemT:
        try:
            self.read(item.id)
            raise ExistsError(item).with_duplicate(
                lambda i: f"_Item with id<{i.id}> already exists."
            )
        except DoesNotExistError:
            with self.connector.connect() as client:
                self.collection(client).insert_one(self.formatter.dump(item))
                return item

    def read(self, item_id: str) -> ItemT:
        with self.connector.connect() as client:
            raw = self.collection(client).find_one({"id": item_id})

            if not raw:
                raise DoesNotExistError(item_id)

            return self.formatter.load(dict(raw))

    def update(self, item: ItemT) -> None:
        with self.connector.connect() as client:
            self.collection(client).find_one_and_update(
                {"id": item.id},
                {"$set": self.formatter.dump(item)},
                return_document=ReturnDocument.AFTER,
            )

    def delete(self, item_id: str) -> None:
        with self.connector.connect() as client:
            result = self.collection(client).delete_one({"id": item_id})

            if result.deleted_count == 0:
                raise DoesNotExistError(item_id)

    def bind(self, **kwargs: Any) -> None:
        pass


class MongoConnector(Protocol):  # pragma: no cover
    def connect(self) -> ContextManager[MongoClient[Any]]:
        pass

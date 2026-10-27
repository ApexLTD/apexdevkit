from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING, Any

from apexdevkit.repository import BruteForceBatch, Entity, Repository

if TYPE_CHECKING:
    from apexdevkit.formatter import Formatter
    from apexdevkit.repository.core.interface import BatchRepository

RawItem = Mapping[str, Any]
RawCollection = Iterable[RawItem]


class RestfulService:  # pragma: no cover
    def create_one(self, item: RawItem) -> RawItem:
        raise NotImplementedError(self.create_one.__name__)

    def read_one(self, item_id: str) -> RawItem:
        raise NotImplementedError(self.read_one.__name__)

    def read_many(self, **params: Any) -> RawCollection:
        raise NotImplementedError(self.read_many.__name__)

    def read_all(self) -> RawCollection:
        raise NotImplementedError(self.read_all.__name__)

    def update_one(self, item_id: str, **with_fields: Any) -> RawItem:
        raise NotImplementedError(self.update_one.__name__)

    def replace_one(self, item: RawItem) -> RawItem:
        raise NotImplementedError(self.replace_one.__name__)

    def delete_one(self, item_id: str) -> None:
        raise NotImplementedError(self.delete_one.__name__)


@dataclass(frozen=True)
class RestfulRepository[ItemT: Entity](RestfulService):
    repository: Repository[ItemT]

    formatter: Formatter[Mapping[str, Any], ItemT]

    @cached_property
    def _batch(self) -> BatchRepository[ItemT]:
        return BruteForceBatch(inner=self.repository)

    def create_one(self, item: RawItem) -> RawItem:
        return self.formatter.dump(self.repository.create(self.formatter.load(item)))

    def read_one(self, item_id: str) -> RawItem:
        return self.formatter.dump(self.repository.read(item_id))

    def read_all(self) -> RawCollection:
        return [self.formatter.dump(item) for item in self.repository]

    def update_one(self, item_id: str, **with_fields: Any) -> RawItem:
        data = dict(self.formatter.dump(self.repository.read(item_id)))
        data.update(**with_fields)

        self.repository.update(self.formatter.load(data))

        return data

    def replace_one(self, item: RawItem) -> RawItem:
        self.repository.update(self.formatter.load(item))

        return item

    def delete_one(self, item_id: str) -> None:
        self.repository.delete(item_id)

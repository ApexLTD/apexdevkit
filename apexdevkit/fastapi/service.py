from abc import ABC
from dataclasses import dataclass, field
from typing import Any, Dict, Generic, Iterable, Self, TypeVar

from apexdevkit.formatter import DataclassFormatter, Formatter
from apexdevkit.repository.interface import Repository

RawItem = dict[str, Any]
RawCollection = Iterable[RawItem]


class _RawItemWithId(Dict[str, Any]):
    def __post_init__(self) -> None:
        assert "id" in self


RawCollectionWithId = Iterable[_RawItemWithId]


class RestfulService(ABC):  # pragma: no cover
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

    def update_many(self, items: RawCollectionWithId) -> RawCollection:
        raise NotImplementedError(self.update_many.__name__)

    def delete_one(self, item_id: str) -> None:
        raise NotImplementedError(self.delete_one.__name__)


ItemT = TypeVar("ItemT")


@dataclass
class RestfulRepositoryBuilder(Generic[ItemT]):
    resource: type[ItemT] | None = field(init=False, default=None)
    formatter: Formatter[ItemT] | None = field(init=False, default=None)
    repository: Repository[Any, ItemT] = field(init=False)

    def with_resource(self, resource: type[ItemT]) -> Self:
        self.resource = resource

        return self

    def with_formatter(self, formatter: Formatter[ItemT]) -> Self:
        self.formatter = formatter

        return self

    def with_repository(self, repository: Repository[Any, ItemT]) -> Self:
        self.repository = repository

        return self

    def build(self) -> RestfulService:
        if not self.formatter and self.resource:
            self.with_formatter(DataclassFormatter(self.resource))

        assert self.formatter, "Must provide either resource or formatter"

        return _RestfulNestedRepository(self.formatter, self.repository)


@dataclass
class _RestfulNestedRepository(RestfulService, Generic[ItemT]):
    formatter: Formatter[ItemT]
    repository: Repository[Any, ItemT]

    def create_one(self, item: RawItem) -> RawItem:
        return self.formatter.dump(self.repository.create(self.formatter.load(item)))

    def create_many(self, items: RawCollection) -> RawCollection:
        return [
            self.formatter.dump(item)
            for item in self.repository.create_many(
                [self.formatter.load(fields) for fields in items]
            )
        ]

    def read_one(self, item_id: str) -> RawItem:
        return self.formatter.dump(self.repository.read(item_id))

    def read_all(self) -> RawCollection:
        return [self.formatter.dump(item) for item in self.repository]

    def update_one(self, item_id: str, **with_fields: Any) -> RawItem:
        data = self.formatter.dump(self.repository.read(item_id))
        data.update(**with_fields)

        self.repository.update(self.formatter.load(data))

        return data

    def update_many(self, items: RawCollectionWithId) -> RawCollection:
        updates = []
        for fields in items:
            data = self.formatter.dump(self.repository.read(fields["id"]))
            data.update(**fields)

            updates.append(self.formatter.load(data))

        self.repository.update_many(updates)

        return [self.formatter.dump(item) for item in updates]

    def delete_one(self, item_id: str) -> None:
        self.repository.delete(item_id)

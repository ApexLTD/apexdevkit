from abc import ABC
from dataclasses import asdict, dataclass, field, replace
from typing import Any, Generic, Iterable, Self, TypeVar

from apexdevkit.formatter import DataclassFormatter, Formatter
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
            self.formatter = DataclassFormatter(self.resource)

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

    def update_many(self, items: RawCollection) -> RawCollection:
        result = [self.formatter.load(fields) for fields in items]

        self.repository.update_many(result)

        return [self.formatter.dump(item) for item in result]

    def delete_one(self, item_id: str) -> None:
        self.repository.delete(item_id)


@dataclass
class RestfulRepository(RestfulService):
    resource: type[Any]
    repository: Repository[Any, Any]

    def create_one(self, item: RawItem) -> RawItem:
        return _as_raw_item(self.repository.create(self.resource(**item)))

    def create_many(self, items: RawCollection) -> RawCollection:
        return _as_raw_collection(
            self.repository.create_many([self.resource(**fields) for fields in items])
        )

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

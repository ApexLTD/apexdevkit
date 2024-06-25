from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4

from fastapi import FastAPI

from apexdevkit.fastapi import FastApiBuilder
from apexdevkit.fastapi.router import RestfulRouter, RestfulServiceBuilder
from apexdevkit.fastapi.schema import SchemaFields
from apexdevkit.fastapi.service import (
    RawCollection,
    RawCollectionWithId,
    RawItem,
    RestfulRepositoryBuilder,
    RestfulService,
)
from apexdevkit.formatter import DataclassFormatter
from apexdevkit.http import JsonDict
from apexdevkit.repository import InMemoryRepository
from apexdevkit.testing import RestfulName


@dataclass
class FakeService(RestfulService):
    always_return: JsonDict
    error: Exception | None = None

    def create_one(self, item: RawItem) -> RawItem:
        self.throw_error()
        return self.always_return

    def create_many(self, items: RawCollection) -> RawCollection:
        self.throw_error()
        return [self.always_return]

    def read_one(self, item_id: str) -> RawItem:
        self.throw_error()
        return self.always_return

    def read_all(self) -> RawCollection:
        self.throw_error()
        return [self.always_return]

    def update_one(self, item_id: str, **with_fields: Any) -> RawItem:
        self.throw_error()
        return self.always_return

    def update_many(self, items: RawCollectionWithId) -> RawCollection:
        self.throw_error()
        return [self.always_return]

    def replace_one(self, item: RawItem) -> RawItem:
        self.throw_error()
        return self.always_return

    def replace_many(self, items: RawCollection) -> RawCollection:
        self.throw_error()
        return [self.always_return]

    def delete_one(self, item_id: str) -> None:
        self.throw_error()

    def throw_error(self) -> None:
        if self.error:
            raise self.error


@dataclass
class FakeServiceBuilder(RestfulServiceBuilder):
    data: JsonDict = field(init=False)
    error: Exception | None = None
    times_called: int = 0

    def with_user(self, user: Any) -> FakeServiceBuilder:
        self.times_called += 1
        self.user = user
        super().with_user(user)

        return self

    def always_return(self, data: JsonDict) -> FakeServiceBuilder:
        self.data = data

        return self

    def with_exception(self, error: Exception | None) -> FakeServiceBuilder:
        self.error = error

        return self

    def build(self) -> RestfulService:
        return FakeService(self.data, self.error)


@dataclass
class SampleServiceBuilder(RestfulServiceBuilder):
    services: dict[str, RestfulService] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.services[""] = (
            RestfulRepositoryBuilder[Apple]()
            .with_formatter(DataclassFormatter(Apple))
            .with_repository(
                InMemoryRepository[Apple]
                .for_dataclass(Apple)
                .with_unique(criteria=lambda item: f"name<{item.name}>")
            )
            .build()
        )

    def with_parent(self, identity: str) -> "RestfulServiceBuilder":
        if identity not in self.services:
            assert self.services[""].read_one(identity)

            self.services[identity] = RestfulPriceService(
                identity,
                InMemoryRepository[Price]
                .for_dataclass(Price)
                .with_unique(criteria=lambda item: f"currency<{item.currecy}>"),
            )

        return super().with_parent(identity)

    def build(self) -> RestfulService:
        return self.services[self.parent_id]


def setup(always_return: JsonDict, error: Exception | None = None) -> FastAPI:
    infra = FakeServiceBuilder().with_exception(error).always_return(always_return)

    return (
        FastApiBuilder()
        .with_title("Apple API")
        .with_version("1.0.0")
        .with_description("Sample API for unit testing various testing routines")
        .with_route(
            apples=RestfulRouter()
            .with_name(RestfulName("apple"))
            .with_fields(AppleFields())
            .with_infra(infra)
            .with_sub_resource(
                prices=(
                    RestfulRouter()
                    .with_name(RestfulName("price"))
                    .with_fields(PriceFields())
                    .with_parent("apple")
                    .with_infra(infra)
                    .with_delete_one_endpoint()
                    .build()
                )
            )
            .default()
            .with_replace_one_endpoint()
            .with_replace_many_endpoint()
            .build()
        )
        .build()
    )


class Color(Enum):
    red = "RED"
    gold = "GOLD"
    green = "GREEN"
    yellow = "YELLOW"
    magenta = "MAGENTA"
    burgundy = "BURGUNDY"


@dataclass(frozen=True)
class Name:
    common: str
    scientific: str


@dataclass(frozen=True)
class Apple:
    name: Name
    color: Color

    id: str = field(default_factory=lambda: str(uuid4()))


class AppleFields(SchemaFields):
    def readable(self) -> JsonDict:
        return JsonDict().with_a(id=str).and_a(name=Name).and_a(color=Color)

    def editable(self) -> JsonDict:
        return JsonDict().with_a(name=Name)


@dataclass(frozen=True)
class Price:
    apple_id: str
    value: int
    exponent: int
    currency: str

    id: str = field(default_factory=lambda: str(uuid4()))


class PriceFields(SchemaFields):
    def readable(self) -> JsonDict:
        return (
            JsonDict()
            .with_a(id=str)
            .and_a(apple_id=str)
            .and_a(value=int)
            .and_a(exponent=int)
            .and_a(currency=str)
        )

    def writable(self) -> JsonDict:
        return self.readable().drop("id", "apple_id")

    def editable(self) -> JsonDict:
        return self.readable().select("value", "exponent")


@dataclass
class RestfulPriceService(RestfulService):
    apple_id: str
    repository: InMemoryRepository[Price]

    def read_all(self) -> RawCollection:
        yield from [asdict(price) for price in self.repository]

    def create_one(self, item: RawItem) -> RawItem:
        price = Price(**item, apple_id=self.apple_id)

        self.repository.create(price)

        return asdict(price)

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from uuid import uuid4

from fastapi import FastAPI

from apexdevkit.fastapi import FastApiBuilder
from apexdevkit.fastapi.router import RestfulRouter, RestfulServiceBuilder
from apexdevkit.fastapi.schema import SchemaFields
from apexdevkit.fastapi.service import (
    RawCollection,
    RawItem,
    RestfulRepositoryBuilder,
    RestfulService,
)
from apexdevkit.formatter import DataclassFormatter
from apexdevkit.http import JsonDict
from apexdevkit.repository import InMemoryRepository
from apexdevkit.testing import RestfulName


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


def setup() -> FastAPI:
    infra = SampleServiceBuilder()
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
                    .with_create_one_endpoint()
                    .with_create_many_endpoint()
                    .with_read_one_endpoint()
                    .with_read_all_endpoint()
                    .with_update_one_endpoint()
                    .with_update_many_endpoint()
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

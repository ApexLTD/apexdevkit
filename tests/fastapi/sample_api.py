from __future__ import annotations

import random
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import Enum
from functools import cached_property
from typing import Any

from fastapi import FastAPI

from apexdevkit.fastapi import FastApiBuilder, RestfulServiceBuilder
from apexdevkit.fastapi.dependable import DependableBuilder
from apexdevkit.fastapi.name import RestfulName
from apexdevkit.fastapi.router import RestfulRouter
from apexdevkit.fastapi.schema import SchemaFields
from apexdevkit.fastapi.service import (
    RawCollection,
    RawCollectionWithId,
    RawItem,
    RestfulService,
)
from apexdevkit.http import JsonDict
from apexdevkit.query import Filter
from apexdevkit.query.query import (
    FooterOptions,
    Operator,
    Page,
    Sort,
    Summary,
)
from apexdevkit.testing.fake import FakeResource


def setup(infra: RestfulServiceBuilder) -> FastAPI:
    dependable = DependableBuilder.from_builder(infra).with_user(lambda: None)

    return (
        FastApiBuilder()
        .with_title("Apple API")
        .with_version("1.0.0")
        .with_description("Sample API for unit testing various testing routines")
        .with_route(
            **{
                "market-apples": RestfulRouter()
                .with_name(RestfulName("market-apple"))
                .with_fields(AppleFields())
                .with_sub_resource(
                    prices=(
                        RestfulRouter()
                        .with_name(RestfulName("price"))
                        .with_fields(PriceFields())
                        .with_delete_one_endpoint(
                            dependable.with_parent(RestfulName("market-apple"))
                        )
                        .build()
                    )
                )
                .with_dependency(dependable)
                .default()
                .with_replace_one_endpoint(dependable)
                .with_replace_many_endpoint(dependable)
                .with_filter_endpoint(dependable)
                .with_aggregation_endpoint(dependable)
                .with_aggregate_endpoint(dependable)
                .build()
            }
        )
        .with_route(
            apples=RestfulRouter()
            .with_name(RestfulName("apple"))
            .with_fields(AppleFields())
            .with_dependency(dependable)
            .with_read_many_endpoint(JsonDict().with_a(color=str))
            .build()
        )
        .build()
    )


@dataclass
class FailingService(RestfulServiceBuilder, RestfulService):
    error: Exception | type[Exception]

    def fail(self, *_: Any, **__: Any) -> Any:
        raise self.error

    def build(self) -> RestfulService:
        return self

    create_one = fail
    create_many = fail
    read_one = fail
    filter_with = fail
    aggregation_with = fail
    sum_with = fail
    read_many = fail
    aggregate_with = fail
    read_all = fail
    update_one = fail
    update_many = fail
    replace_one = fail
    replace_many = fail
    delete_one = fail


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
    id: str
    name: Name
    color: Color


class AppleFields(SchemaFields):
    def readable(self) -> JsonDict:
        return (
            JsonDict()
            .with_a(id=str)
            .and_a(name=JsonDict().with_a(common=str).and_a(scientific=str))
            .and_a(color=str)
        )

    def editable(self) -> JsonDict:
        return JsonDict().with_a(
            name=JsonDict().with_a(common=str).and_a(scientific=str)
        )

    def filters(self) -> JsonDict:
        return (
            JsonDict()
            .with_a(filter=Filter | None)
            .and_a(condition=Operator | None)
            .and_a(ordering=list[Sort])
            .and_a(paging=Page)
        )

    def aggregation_filters(self) -> JsonDict:
        return JsonDict().with_a(is_rotten=bool)


class PriceFields(SchemaFields):
    def readable(self) -> JsonDict:
        return JsonDict().with_a(id=str).and_a(value=int)


@dataclass(frozen=True)
class FakeApple(FakeResource[Apple]):
    id: str | None = None
    name: Name | None = None
    item_type: type[Apple] = field(default=Apple)

    @cached_property
    def _raw(self) -> dict[str, Any]:
        return {
            "id": self.id or self.fake.uuid(),
            "name": self._name(),
            "color": random.choice(list(Color)).value,
        }

    def _name(self) -> dict[str, Any]:
        name = self.name or Name(self.fake.text(length=10), self.fake.text(length=10))
        return {"scientific": name.scientific, "common": name.common}


@dataclass
class SuccessfulService(RestfulServiceBuilder, RestfulService):
    always_return: JsonDict
    called_with: Any | None = None

    def build(self) -> RestfulService:
        return self

    def create_one(self, item: RawItem) -> RawItem:
        self.called_with = item
        return self.always_return

    def create_many(self, items: RawCollection) -> RawCollection:
        self.called_with = items
        return [self.always_return]

    def read_one(self, item_id: str) -> RawItem:
        self.called_with = item_id
        return self.always_return

    def read_many(self, **params: Any) -> RawCollection:
        self.called_with = params
        return [self.always_return]

    def filter_with(self, options: RawItem) -> RawCollection:
        self.called_with = options
        return [self.always_return]

    def aggregation_with(self, options: RawItem) -> RawItem:
        self.called_with = options
        return {"count": 1, "sums": []}

    def read_all(self) -> RawCollection:
        self.called_with = None
        return [self.always_return]

    def aggregate_with(self, options: FooterOptions) -> Iterable[Summary]:
        self.called_with = options
        return []

    def update_one(self, item_id: str, **with_fields: Any) -> RawItem:
        self.called_with = (item_id, with_fields)
        return self.always_return

    def update_many(self, items: RawCollectionWithId) -> RawCollection:
        self.called_with = items
        return [self.always_return]

    def replace_one(self, item: RawItem) -> RawItem:
        self.called_with = item
        return self.always_return

    def replace_many(self, items: RawCollection) -> RawCollection:
        self.called_with = items
        return [self.always_return]

    def delete_one(self, item_id: str) -> None:
        self.called_with = item_id

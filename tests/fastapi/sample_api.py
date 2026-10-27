from __future__ import annotations

import random
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from enum import Enum
from functools import cached_property
from typing import TYPE_CHECKING, Any

from pypebbles import JsonDict

from apexdevkit.fastapi import FastApiBuilder, RestfulRouter, RestfulServiceBuilder
from apexdevkit.fastapi.schema import SchemaFields
from apexdevkit.fastapi.service import (
    RestfulService,
    RestfulServiceWithFormatter,
)
from apexdevkit.formatter import DataclassFormatter
from apexdevkit.repository import Entity
from tests.fake import Fake

if TYPE_CHECKING:
    from collections.abc import Iterable

    from fastapi import FastAPI

    from apexdevkit.fastapi.dependable import DependableBuilder


def setup(dependency: DependableBuilder) -> FastAPI:
    return (
        FastApiBuilder()
        .with_title("Apple API")
        .with_version("1.0.0")
        .with_description("Sample API for unit testing various testing routines")
        .with_route(
            apples=RestfulRouter.named("apple")
            .with_fields(AppleFields())
            .with_default_dependency(dependency)
            .with_read_one()
            .with_create_one()
            .with_update_one()
            .with_replace_one()
            .with_delete_one()
            .with_read_many(JsonDict().with_a(color=str))
            .with_sub_resource(
                prices=RestfulRouter.named("price")
                .child_of("apple")
                .with_fields(PriceFields())
                .with_default_dependency(dependency)
                .default()
                .build()
            )
            .build()
        )
        .build()
    )


@dataclass
class FailingService(RestfulServiceBuilder):
    error: Exception | type[Exception]

    def fail(self, *_: Any, **__: Any) -> Any:
        raise self.error

    def build(self) -> RestfulService:
        return RestfulServiceWithFormatter(
            inner=self,
            formatter=DataclassFormatter(Apple),
        )

    create_one = fail
    read_one = fail
    read_many = fail
    read_all = fail
    update_one = fail
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
class Apple(Entity):
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
        return self.readable().select("name")


class PriceFields(SchemaFields):
    def readable(self) -> JsonDict:
        return JsonDict().with_a(id=str).and_a(value=int)


@dataclass(frozen=True)
class FakeApple:
    id: str | None = None
    name: Name | None = None
    fake: Fake = field(default_factory=Fake)

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

    def unknown_id(self) -> str:
        return self.fake.text(length=32)

    def json(self) -> JsonDict:
        return JsonDict(self._raw)

    def entity(self, **fields: Any) -> Apple:
        return AppleFormatter().load(self.json().merge(JsonDict(fields)))


class AppleFormatter:
    def load(self, source: Mapping[str, Any]) -> Apple:
        return Apple(
            name=Name(
                common=source["name"]["common"],
                scientific=source["name"]["scientific"],
            ),
            color=Color(source["color"]),
        )

    def dump(self, target: Apple) -> Mapping[str, Any]:
        return {
            "id": target.id,
            "name": {
                "scientific": target.name.scientific,
                "common": target.name.common,
            },
            "color": target.color.value,
        }


@dataclass
class SuccessfulService(RestfulServiceBuilder):
    always_return: JsonDict
    called_with: Any | None = None

    @property
    def formatter(self) -> AppleFormatter:
        return AppleFormatter()

    def apple(self) -> Apple:
        return replace(
            self.formatter.load(self.always_return),
            id=self.always_return["id"],
        )

    def build(self) -> RestfulService:
        return RestfulServiceWithFormatter(inner=self, formatter=self.formatter)

    def create_one(self, item: Apple) -> Apple:
        self.called_with = item

        return self.apple()

    def read_one(self, with_id: str) -> Apple:
        self.called_with = with_id

        return self.apple()

    def read_many(self, query: JsonDict) -> Iterable[Apple]:
        self.called_with = query

        return [self.apple()]

    def read_all(self) -> Iterable[Apple]:
        self.called_with = None

        return [self.apple()]

    def update_one(self, item: Apple) -> Apple:
        self.called_with = item

        return self.apple()

    def replace_one(self, item: Apple) -> Apple:
        self.called_with = item

        return self.apple()

    def delete_one(self, with_id: str) -> Apple:
        self.called_with = with_id

        return self.apple()

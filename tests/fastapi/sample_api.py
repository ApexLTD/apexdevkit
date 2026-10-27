from __future__ import annotations

import random
from dataclasses import dataclass, field, replace
from enum import Enum
from functools import cached_property
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

from pypebbles import JsonDict

from apexdevkit.fastapi import FastApiBuilder, RestfulRouter
from apexdevkit.fastapi.schema import SchemaFields
from apexdevkit.repository import Entity
from tests.fake import Fake

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

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
    fake: Fake = field(default_factory=Fake)

    @cached_property
    def _raw(self) -> dict[str, Any]:
        return {
            "id": self.fake.uuid(),
            "name": {
                "scientific": self.fake.text(length=10),
                "common": self.fake.text(length=10),
            },
            "color": random.choice(list(Color)).value,
        }

    def unknown_id(self) -> str:
        return self.fake.text(length=32)

    def json(self) -> JsonDict:
        return JsonDict(self._raw)

    def entity(self, **fields: Any) -> Apple:
        return AppleFormatter().load(self.json().merge(JsonDict(fields)))


class AppleFormatter:
    def load(self, source: Mapping[str, Any]) -> Apple:
        result = Apple(
            name=Name(
                common=source["name"]["common"],
                scientific=source["name"]["scientific"],
            ),
            color=Color(source["color"]),
        )

        return replace(result, id=source.get("id", result.id))

    def dump(self, target: Apple) -> Mapping[str, Any]:
        return {
            "id": target.id,
            "name": {
                "scientific": target.name.scientific,
                "common": target.name.common,
            },
            "color": target.color.value,
        }


@dataclass(frozen=True)
class SuccessfulService:
    always_return: Apple

    log: MagicMock = field(default_factory=MagicMock)

    def create_one(self, item: Apple) -> Apple:
        self.log(create_one=item)

        return self.always_return

    def read_one(self, with_id: str) -> Apple:
        self.log(read_one=with_id)

        return self.always_return

    def read_many(self, query: JsonDict) -> Iterable[Apple]:
        self.log(read_many=query)

        return [self.always_return]

    def read_all(self) -> Iterable[Apple]:
        self.log(read_all=None)

        return [self.always_return]

    def update_one(self, item: Apple) -> Apple:
        self.log(update_one=item)

        return self.always_return

    def replace_one(self, item: Apple) -> Apple:
        self.log(replace_one=item)

        return self.always_return

    def delete_one(self, with_id: str) -> Apple:
        self.log(delete_one=with_id)

        return self.always_return


@dataclass(frozen=True)
class FailingService:
    error: Exception | type[Exception]

    def fail(self, *_: Any, **__: Any) -> Any:
        raise self.error

    create_one = fail
    read_one = fail
    read_many = fail
    read_all = fail
    update_one = fail
    delete_one = fail

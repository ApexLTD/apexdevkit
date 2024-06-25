from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4

from apexdevkit.fastapi.router import RestfulServiceBuilder
from apexdevkit.fastapi.schema import SchemaFields
from apexdevkit.fastapi.service import (
    RawCollection,
    RawCollectionWithId,
    RawItem,
    RestfulService,
)
from apexdevkit.http import JsonDict


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


class PriceFields(SchemaFields):
    def readable(self) -> JsonDict:
        return JsonDict().with_a(id=str).and_a(value=int)

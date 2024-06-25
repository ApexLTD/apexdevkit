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
class FailingService(RestfulServiceBuilder, RestfulService):
    error: Exception | type[Exception]

    def build(self) -> RestfulService:
        return self

    def create_one(self, item: RawItem) -> RawItem:
        raise self.error

    def create_many(self, items: RawCollection) -> RawCollection:
        raise self.error

    def read_one(self, item_id: str) -> RawItem:
        raise self.error

    def read_all(self) -> RawCollection:
        raise self.error

    def update_one(self, item_id: str, **with_fields: Any) -> RawItem:
        raise self.error

    def update_many(self, items: RawCollectionWithId) -> RawCollection:
        raise self.error

    def replace_one(self, item: RawItem) -> RawItem:
        raise self.error

    def replace_many(self, items: RawCollection) -> RawCollection:
        raise self.error

    def delete_one(self, item_id: str) -> None:
        raise self.error


@dataclass
class SuccessfulService(RestfulServiceBuilder, RestfulService):
    always_return: JsonDict

    def build(self) -> RestfulService:
        return self

    def create_one(self, item: RawItem) -> RawItem:
        return self.always_return

    def create_many(self, items: RawCollection) -> RawCollection:
        return [self.always_return]

    def read_one(self, item_id: str) -> RawItem:
        return self.always_return

    def read_all(self) -> RawCollection:
        return [self.always_return]

    def update_one(self, item_id: str, **with_fields: Any) -> RawItem:
        return self.always_return

    def update_many(self, items: RawCollectionWithId) -> RawCollection:
        return [self.always_return]

    def replace_one(self, item: RawItem) -> RawItem:
        return self.always_return

    def replace_many(self, items: RawCollection) -> RawCollection:
        return [self.always_return]

    def delete_one(self, item_id: str) -> None:
        pass


@dataclass
class FakeServiceBuilder(RestfulServiceBuilder):
    data: JsonDict = field(init=False)
    times_called: int = 0

    def with_user(self, user: Any) -> FakeServiceBuilder:
        self.times_called += 1
        self.user = user
        super().with_user(user)

        return self

    def always_return(self, data: JsonDict) -> FakeServiceBuilder:
        self.data = data

        return self

    def build(self) -> RestfulService:
        return SuccessfulService(always_return=self.data)


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

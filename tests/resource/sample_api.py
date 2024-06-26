from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4

from apexdevkit.fastapi.builder import RestfulServiceBuilder
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

    def read_all(self) -> RawCollection:
        self.called_with = None
        return [self.always_return]

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
        return JsonDict().with_a(id=str).and_a(name=Name).and_a(color=str)

    def editable(self) -> JsonDict:
        return JsonDict().with_a(name=Name)


class PriceFields(SchemaFields):
    def readable(self) -> JsonDict:
        return JsonDict().with_a(id=str).and_a(value=int)

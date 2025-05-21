from __future__ import annotations

import random
from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, Generic, TypeVar

from faker import Faker

from apexdevkit.http import JsonDict
from apexdevkit.query.query import (
    Aggregation,
    AggregationOption,
    DateValue,
    Filter,
    Leaf,
    NumericValue,
    Operation,
    Operator,
    Page,
    QueryOptions,
    Sort,
    StringValue,
)
from apexdevkit.value import Value

ItemT = TypeVar("ItemT")


@dataclass(frozen=True)
class Fake:
    faker: Faker = field(default_factory=Faker)

    def uuid(self) -> str:
        return str(self.faker.uuid4())

    def text(self, *, length: int) -> str:
        return "".join(self.faker.random_letters(length=length))

    def number(self, top: int = 100000) -> int:
        return int(self.faker.random.randint(0, top))

    def timestamp(self) -> int:
        return int(self.faker.unix_time())

    def minute(self) -> int:
        return int(self.faker.random_int(min=0, max=59))

    def hour(self) -> int:
        return int(self.faker.random_int(min=0, max=23))

    def first_name(self) -> str:
        return str(self.faker.first_name())

    def last_name(self) -> str:
        return str(self.faker.last_name())

    def sentence(self, *, words: int) -> str:
        return str(self.faker.sentence(nb_words=words))

    def country(self) -> str:
        return str(self.faker.country())

    def address(self) -> str:
        return str(self.faker.address())

    def bool(self) -> bool:
        return bool(self.faker.boolean())


@dataclass(frozen=True)
class FakeResource(Generic[ItemT]):
    item_type: type[ItemT] = field()
    fake: Fake = field(default_factory=Fake)

    @cached_property
    def _raw(self) -> dict[str, Any]:
        return {}

    def unknown_id(self) -> str:
        return self.fake.text(length=32)

    def json(self) -> JsonDict:
        return JsonDict(self._raw)

    def entity(self, **fields: Any) -> ItemT:
        return self.item_type(**self.json().merge(JsonDict(fields)))


@dataclass(frozen=True)
class FakeValue(FakeResource[Value]):
    item_type: type[Value] = field(default=Value)

    @cached_property
    def _raw(self) -> dict[str, Any]:
        return {
            "value": self.fake.number(),
            "exponent": random.choice([10, 100, 1000]),
        }


@dataclass(frozen=True)
class FakeNumericValue(FakeResource[NumericValue]):
    item_type: type[NumericValue] = field(default=NumericValue)

    @cached_property
    def _raw(self) -> dict[str, Any]:
        return {
            "value": self.fake.number(),
            "exponent": 100,
        }


@dataclass(frozen=True)
class FakeStringValue(FakeResource[StringValue]):
    item_type: type[StringValue] = field(default=StringValue)

    @cached_property
    def _raw(self) -> dict[str, Any]:
        return {
            "value": self.fake.text(length=6),
        }


@dataclass(frozen=True)
class FakeDateValue(FakeResource[DateValue]):
    item_type: type[DateValue] = field(default=DateValue)

    @cached_property
    def _raw(self) -> dict[str, Any]:
        return {"date": "2021/12/12T00:00:00"}


@dataclass(frozen=True)
class FakeLeaf(FakeResource[Leaf]):
    values: list[NumericValue | StringValue | DateValue] = field(default_factory=list)
    item_type: type[Leaf] = field(default=Leaf)

    @cached_property
    def _raw(self) -> dict[str, Any]:
        return {
            "name": self.fake.text(length=8),
            "values": self.values,
        }


@dataclass(frozen=True)
class FakeOperator(FakeResource[Operator]):
    operands: list[Operator | Leaf] = field(default_factory=list)
    item_type: type[Operator] = field(default=Operator)

    @cached_property
    def _raw(self) -> dict[str, Any]:
        return {
            "operation": Operation.EQUALS,
            "operands": self.operands,
        }


@dataclass(frozen=True)
class FakeSort(FakeResource[Sort]):
    is_descending: bool | None = None
    item_type: type[Sort] = field(default=Sort)

    @cached_property
    def _raw(self) -> dict[str, Any]:
        return {
            "name": self.fake.text(length=7),
            "is_descending": self.is_descending
            if self.is_descending is not None
            else self.fake.bool(),
        }


@dataclass(frozen=True)
class FakePage(FakeResource[Page]):
    item_type: type[Page] = field(default=Page)

    @cached_property
    def _raw(self) -> dict[str, Any]:
        return {
            "page": self.fake.number(top=10),
            "length": self.fake.number(top=500),
            "offset": self.fake.number(top=500),
        }


@dataclass(frozen=True)
class FakeFilter(FakeResource[Filter]):
    args: list[NumericValue | StringValue] = field(default_factory=list)
    item_type: type[Filter] = field(default=Filter)

    @cached_property
    def _raw(self) -> dict[str, Any]:
        return {
            "args": self.args,
        }


@dataclass(frozen=True)
class FakeQueryOptions(FakeResource[QueryOptions]):
    filter: Filter | None = None
    condition: Operator | None = None
    ordering: list[Sort] = field(default_factory=list)
    paging: Page | None = None
    item_type: type[QueryOptions] = field(default=QueryOptions)

    @cached_property
    def _raw(self) -> dict[str, Any]:
        return {
            "filter": self.filter or FakeFilter().entity(),
            "condition": self.condition,
            "ordering": self.ordering,
            "paging": self.paging or FakePage().entity(),
        }


@dataclass(frozen=True)
class FakeAggregationOption(FakeResource[AggregationOption]):
    item_type: type[AggregationOption] = field(default=AggregationOption)

    @cached_property
    def _raw(self) -> dict[str, Any]:
        return {"name": self.fake.text(length=8), "aggregation": Aggregation.COUNT}

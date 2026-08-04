from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from typing import Any

from apexdevkit.query import (
    Aggregation,
    AggregationOption,
    DateValue,
    Filter,
    Leaf,
    NumericValue,
    Operation,
    Operator,
    Page,
    Sort,
    StringValue,
)
from apexdevkit.testing.fake import FakeResource


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
            else self.fake.boolean(),
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
class FakeAggregationOption(FakeResource[AggregationOption]):
    item_type: type[AggregationOption] = field(default=AggregationOption)

    @cached_property
    def _raw(self) -> dict[str, Any]:
        return {"name": self.fake.text(length=8), "aggregation": Aggregation.COUNT}

from __future__ import annotations

import random
from dataclasses import dataclass, field
from decimal import Decimal
from functools import cached_property
from typing import Any, Type

from apexdevkit.formatter import DataclassFormatter
from apexdevkit.testing.fake import FakeResource


@dataclass(frozen=True)
class Value:
    value: int = 0
    exponent: int = 1

    def as_decimal(self) -> Decimal:
        return Decimal(self.value) / Decimal(self.exponent)

    @classmethod
    def from_string(cls, decimal_str: str) -> Value:
        integer_part, _, fractional_part = decimal_str.partition(".")
        value = int(integer_part + fractional_part)
        exponent = 10 ** len(fractional_part)
        return cls(value, exponent)

    def add(self, other: Value) -> Value:
        return Value(self.value + self._adjusted(other), self.exponent)

    def subtract(self, other: Value) -> Value:
        return Value(self.value - self._adjusted(other), self.exponent)

    def _adjusted(self, other: Value) -> int:
        return int(Decimal(other.value) / Decimal(other.exponent) * self.exponent)


@dataclass(frozen=True)
class FakeValue(FakeResource[Value]):
    item_type: Type[Value] = field(default=Value)

    @cached_property
    def _raw(self) -> dict[str, Any]:
        return {
            "value": self.fake.number(),
            "exponent": random.choice([10, 100, 1000]),
        }


class ValueFormatter:
    def load(self, raw: dict[str, Any]) -> Value:
        return DataclassFormatter(Value).load(raw)

    def dump(self, value: Value) -> dict[str, Any]:
        return DataclassFormatter(Value).dump(value)

from __future__ import annotations

import random
from dataclasses import dataclass, field
from decimal import Decimal
from functools import cached_property
from typing import Any, Type

from apexdevkit.testing.fake import FakeResource


@dataclass(frozen=True)
class Quantity:
    value: int = 0
    exponent: int = 1

    def as_decimal(self) -> Decimal:
        return Decimal(self.value) / Decimal(self.exponent)

    @classmethod
    def from_string(cls, decimal_str: str) -> Quantity:
        integer_part, _, fractional_part = decimal_str.partition(".")
        value = int(integer_part + fractional_part)
        exponent = 10 ** len(fractional_part)
        return cls(value, exponent)

    def add(self, other: Quantity) -> Quantity:
        return Quantity(self.value + self._adjusted(other), self.exponent)

    def subtract(self, other: Quantity) -> Quantity:
        return Quantity(self.value - self._adjusted(other), self.exponent)

    def _adjusted(self, other: Quantity) -> int:
        return int(Decimal(other.value) / Decimal(other.exponent) * self.exponent)


@dataclass(frozen=True)
class Value:
    value: int = 0
    exponent: int = 1

    unit: str = "unknown"

    def as_decimal(self) -> Decimal:
        return Decimal(self.value) / Decimal(self.exponent)

    def as_quantity(self) -> Quantity:
        return Quantity(self.value, self.exponent)

    @classmethod
    def from_string(cls, decimal_str: str) -> Value:
        quantity = Quantity.from_string(decimal_str)
        return cls(quantity.value, quantity.exponent)

    def add(self, other: Value) -> Value:
        return Value(
            self.as_quantity().add(other.as_quantity()).value, self.exponent, self.unit
        )

    def subtract(self, other: Value) -> Value:
        return Value(
            self.as_quantity().subtract(other.as_quantity()).value,
            self.exponent,
            self.unit,
        )

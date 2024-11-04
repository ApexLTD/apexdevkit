from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


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

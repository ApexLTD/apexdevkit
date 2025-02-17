from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Value:
    value: int = 0
    exponent: int = 1

    unit: str = "unknown"

    def as_decimal(self) -> Decimal:
        return Decimal(self.value) / Decimal(self.exponent)

    @classmethod
    def from_string(cls, decimal_str: str) -> Value:
        integer_part, _, fractional_part = decimal_str.partition(".")
        value = int(integer_part + fractional_part)
        exponent = 10 ** len(fractional_part)

        return cls(value, exponent)

    def add(self, other: Value) -> Value:
        exponent = self.exponent * other.exponent
        value = self.value * other.exponent + self.exponent * other.value
        gcd = int(math.gcd(exponent, value))

        return Value(int(value / gcd), int(exponent / gcd))

    def subtract(self, other: Value) -> Value:
        exponent = self.exponent * other.exponent
        value = self.value * other.exponent - self.exponent * other.value
        gcd = int(math.gcd(exponent, value))

        return Value(int(value / gcd), int(exponent / gcd))

    def multiply(self, other: Value) -> Value:
        exponent = self.exponent * other.exponent
        value = self.value * other.value
        gcd = int(math.gcd(exponent, value))

        return Value(int(value / gcd), int(exponent / gcd))

    def divide(self, other: Value) -> Value:
        exponent = self.exponent * other.value
        value = self.value * other.exponent
        gcd = int(math.gcd(exponent, value))

        return Value(int(value / gcd), int(exponent / gcd))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Value):
            return self.as_decimal() == other.as_decimal()

        if isinstance(other, Decimal):
            return self.as_decimal() == other

        return False  # pragma: no cover

    def __float__(self) -> float:
        return float(self.as_decimal())

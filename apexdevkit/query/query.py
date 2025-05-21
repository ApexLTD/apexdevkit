from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Any


@dataclass
class FooterOptions:
    filter: Filter | None
    condition: Operator | None
    aggregations: list[AggregationOption]


@dataclass
class QueryOptions:
    filter: Filter | None
    condition: Operator | None
    ordering: list[Sort]
    paging: Page


@dataclass
class AggregationOption:
    name: str | None
    aggregation: Aggregation


@dataclass
class Sort:
    name: str
    is_descending: bool


@dataclass
class Page:
    page: int | None
    length: int | None
    offset: int | None


@dataclass
class Summary:
    name: str | None
    aggregation: Aggregation
    result: NumericValue | StringValue | DateValue | NullValue


@dataclass
class SummaryExtractor:
    aggregation: AggregationOption

    def with_value(self, value: Any) -> Summary:
        return Summary(
            self.aggregation.name, self.aggregation.aggregation, self._value(value)
        )

    def _value(self, value: Any) -> NumericValue | DateValue | StringValue | NullValue:
        if value is None:
            return NullValue()
        if isinstance(value, int | float | Decimal):
            return NumericValue.from_decimal(Decimal(value))
        if self.aggregation.name and (
            "date" in self.aggregation.name.lower()
            or "time" in self.aggregation.name.lower()
        ):
            return DateValue(str(value))
        return StringValue(str(value))


@dataclass
class NumericValue:
    value: int
    exponent: int = 1

    def eval(self) -> str:
        return str(self.value / self.exponent)

    def as_arg(self) -> str:
        return self.eval()

    @classmethod
    def from_decimal(cls, value: Decimal) -> NumericValue:
        exponent = 10 ** (len(str(value).split(".")[1]) - 1) if "." in str(value) else 1
        return cls(value=int(Decimal(value) * exponent), exponent=exponent)


@dataclass
class StringValue:
    value: str

    def eval(self) -> str:
        return f"N'{self.value}'"

    def as_arg(self) -> str:
        return f"'{self.value}'"


@dataclass
class DateValue:
    date: str

    def eval(self) -> str:
        date = self.date.replace("T", " ")
        return f"convert(datetime, '{date}.000', 121)"

    def as_arg(self) -> str:
        return f"'{self.date[:10]}'"


@dataclass
class ListValue:
    values: list[NumericValue | StringValue | DateValue]

    def as_arg(self) -> str:
        args = ",".join(arg.as_arg()[1:-1] for arg in self.values)
        return f"'{args}'"


@dataclass(frozen=True)
class NullValue:
    pass


@dataclass
class Leaf:
    name: str
    values: list[NumericValue | StringValue | DateValue]


@dataclass
class Operator:
    operation: Operation
    operands: list[Operator | Leaf]


@dataclass
class Filter:
    args: list[NumericValue | StringValue | DateValue | ListValue | None]


class Operation(Enum):
    BETWEEN = "BETWEEN"
    RANGE = "RANGE"
    NULL = "NULL"
    BLANK = "BLANK"
    IN = "IN"
    CONTAINS = "CONTAINS"
    LIKE = "LIKE"
    BEGINS = "BEGINS"
    ENDS = "ENDS"
    EQUALS = "="
    NOT_EQUALS = "<>"
    GREATER = ">"
    GREATER_OR_EQUALS = ">="
    LESS = "<"
    LESS_OR_EQUALS = "<="
    AND = "AND"
    OR = "OR"
    NOT = "NOT"


class Aggregation(Enum):
    COUNT = "COUNT"
    MAX = "MAX"
    MIN = "MIN"
    SUM = "SUM"
    AVG = "AVG"

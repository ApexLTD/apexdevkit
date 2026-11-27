from apexdevkit.query.query import (
    Aggregation,
    AggregationOption,
    DateValue,
    Filter,
    FooterOptions,
    Leaf,
    ListValue,
    NullValue,
    NumericValue,
    Operation,
    Operator,
    Page,
    QueryOptions,
    Sort,
    StringValue,
    Summary,
)

__all__ = [
    "Aggregation",
    "AggregationOption",
    "DateValue",
    "Filter",
    "FooterOptions",
    "Leaf",
    "ListValue",
    "NullValue",
    "NumericValue",
    "Operation",
    "Operator",
    "Page",
    "QueryOptions",
    "Sort",
    "StringValue",
    "Summary",
]

from apexdevkit.annotation import notify

notify("apexdevkit.query is deprecated, will be removed in future versions")

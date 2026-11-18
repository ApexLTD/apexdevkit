from dataclasses import dataclass

from apexdevkit.query import (
    Aggregation,
    AggregationOption,
    FooterOptions,
    Leaf,
    Operation,
    Operator,
    Page,
    QueryOptions,
    Sort,
    StringValue,
)
from apexdevkit.query.generator import MsSqlField, MsSqlQueryBuilder
from pytest_apex import ApprovalCase
from apexdevkit.repository.core import DatabaseCommand


def test_filter_query(approve: ApprovalCase) -> None:
    approve.sql().compact(_Target().filter_query().value)


def test_filter_payload(approve: ApprovalCase) -> None:
    approve.json().mapping(_Target().filter_query().payload)


def test_aggregate_query(approve: ApprovalCase) -> None:
    approve.sql().compact(_Target().aggregation_query().value)


def test_aggregate_payload(approve: ApprovalCase) -> None:
    approve.json().mapping(_Target().aggregation_query().payload)


@dataclass(frozen=True)
class _Target:
    source: str = "TABLE"
    username: str = "John"

    def builder(self) -> MsSqlQueryBuilder:
        return (
            MsSqlQueryBuilder()
            .with_source(self.source)
            .with_username(self.username)
            .with_fields(
                [
                    MsSqlField("item_id", alias="id"),
                    MsSqlField("item_name", alias="name"),
                    MsSqlField("date"),
                ]
            )
        )

    def filter_query(self) -> DatabaseCommand:
        return self.builder().filter(
            QueryOptions(
                filter=None,
                condition=Operator(
                    Operation.OR,
                    operands=[
                        Operator(
                            Operation.BEGINS,
                            operands=[Leaf("id", values=[StringValue("begin")])],
                        ),
                        Operator(
                            Operation.ENDS,
                            operands=[Leaf("name", values=[StringValue("end")])],
                        ),
                    ],
                ),
                ordering=[Sort("date", is_descending=True)],
                paging=Page(20, 100, 500),
            )
        )

    def aggregation_query(self) -> DatabaseCommand:
        return self.builder().aggregate(
            FooterOptions(
                filter=None,
                condition=Operator(
                    Operation.OR,
                    operands=[
                        Operator(
                            Operation.BEGINS,
                            operands=[Leaf("id", values=[StringValue("begin")])],
                        ),
                        Operator(
                            Operation.ENDS,
                            operands=[Leaf("name", values=[StringValue("end")])],
                        ),
                    ],
                ),
                aggregations=[AggregationOption("name", Aggregation.COUNT)],
            )
        )

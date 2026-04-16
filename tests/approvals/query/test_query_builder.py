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
from tests.approvals.conftest import Approver


def test_filter(approver: Approver) -> None:
    builder = (
        MsSqlQueryBuilder()
        .with_source("TABLE")
        .with_username("John")
        .with_fields(
            [
                MsSqlField("item_id", alias="id"),
                MsSqlField("item_name", alias="name"),
                MsSqlField("date"),
            ]
        )
    )

    query = builder.filter(
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

    approver.verify_sql("filter", query.value)


def test_aggregate(approver: Approver) -> None:
    builder = (
        MsSqlQueryBuilder()
        .with_source("TABLE")
        .with_username("John")
        .with_fields(
            [
                MsSqlField("item_id", alias="id"),
                MsSqlField("item_name", alias="name"),
                MsSqlField("date"),
            ]
        )
    )

    query = builder.aggregate(
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

    approver.verify_sql("aggregate", query.value)

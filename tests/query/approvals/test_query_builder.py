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
from tests.query.approvals.extension import verify_sql


def test_filter() -> None:
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

    verify_sql(str(query))


def test_aggregate() -> None:
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

    verify_sql(str(query))

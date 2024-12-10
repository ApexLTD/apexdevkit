import pytest

from apexdevkit.error import ForbiddenError
from apexdevkit.query import Aggregation, AggregationOption
from apexdevkit.query.generator import MsSqlField, MsSqlFooterGenerator
from apexdevkit.testing.fake import FakeAggregationOption


def test_should_select_footer() -> None:
    option = FakeAggregationOption().entity()
    fields = [MsSqlField("name", option.name or "")]

    assert (
        MsSqlFooterGenerator([option], fields).generate()
        == f"SELECT {option.aggregation.value}(name) AS "
        f"{option.name}_{option.aggregation.value.lower()}"
    )


def test_should_select_footers() -> None:
    options = [FakeAggregationOption().entity(), FakeAggregationOption().entity()]
    fields = [
        MsSqlField("name_0", alias=options[0].name or ""),
        MsSqlField("name_1", alias=options[1].name or ""),
    ]

    assert (
        MsSqlFooterGenerator(options, fields).generate()
        == f"SELECT {options[0].aggregation.value}(name_0) AS "
        f"{options[0].name}_{options[0].aggregation.value.lower()}, "
        f"{options[1].aggregation.value}(name_1) AS "
        f"{options[1].name}_{options[1].aggregation.value.lower()}"
    )


def test_should_fail_for_unknown_field() -> None:
    with pytest.raises(ForbiddenError):
        MsSqlFooterGenerator(
            aggregations=[FakeAggregationOption().entity()],
            fields=[MsSqlField("name", alias="name")],
        ).generate()


def test_should_aggregate_without_name() -> None:
    generator = MsSqlFooterGenerator(
        aggregations=[
            AggregationOption(
                name=None,
                aggregation=Aggregation.COUNT,
            )
        ],
        fields=[MsSqlField("name", alias="name")],
    )

    assert generator.generate() == "SELECT COUNT(*) AS general_count"

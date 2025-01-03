import pytest

from apexdevkit.error import ForbiddenError
from apexdevkit.query import Aggregation, AggregationOption
from apexdevkit.query.generator import MsSqlField, MsSqlFooterGenerator
from apexdevkit.testing.fake import FakeAggregationOption


def test_should_select_footer() -> None:
    option = FakeAggregationOption().entity()
    generator = MsSqlFooterGenerator(
        aggregations=[option],
        fields=[MsSqlField("name", option.name or "")],
    )

    assert (
        generator.generate() == f"SELECT {option.aggregation.value}(name) AS "
        f"{option.name}_{option.aggregation.value.lower()}"
    )


def test_should_select_footers() -> None:
    options = [FakeAggregationOption().entity(), FakeAggregationOption().entity()]
    generator = MsSqlFooterGenerator(
        aggregations=options,
        fields=[
            MsSqlField("name_0", alias=options[0].name or ""),
            MsSqlField("name_1", alias=options[1].name or ""),
        ],
    )

    assert (
        generator.generate() == f"SELECT {options[0].aggregation.value}(name_0) AS "
        f"{options[0].name}_{options[0].aggregation.value.lower()}, "
        f"{options[1].aggregation.value}(name_1) AS "
        f"{options[1].name}_{options[1].aggregation.value.lower()}"
    )


def test_should_fail_for_unknown_field() -> None:
    generator = MsSqlFooterGenerator(
        aggregations=[FakeAggregationOption().entity()],
        fields=[],
    )

    with pytest.raises(ForbiddenError):
        generator.generate()


def test_should_aggregate_without_name() -> None:
    generator = MsSqlFooterGenerator(
        aggregations=[
            AggregationOption(
                name=None,
                aggregation=Aggregation.COUNT,
            )
        ],
        fields=[MsSqlField("name")],
    )

    assert generator.generate() == "SELECT COUNT(*) AS general_count"

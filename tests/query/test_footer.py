from apexdevkit.query.generator import MsSqlFooterGenerator
from apexdevkit.testing.fake import FakeAggregationOption


def test_should_select_footer() -> None:
    option = FakeAggregationOption().entity()
    translation: dict[str, str] = {option.name: "name"}  # type: ignore

    assert (
        MsSqlFooterGenerator([option], translation).generate()
        == f"SELECT {option.aggregation.value}(name) AS "
        f"{option.name}_{option.aggregation.value.lower()}"
    )


def test_should_select_footers() -> None:
    options = [FakeAggregationOption().entity(), FakeAggregationOption().entity()]
    translation: dict[str, str] = {
        options[0].name: "name_0",  # type: ignore
        options[1].name: "name_1",  # type: ignore
    }

    assert (
        MsSqlFooterGenerator(options, translation).generate()
        == f"SELECT {options[0].aggregation.value}(name_0) AS "
        f"{options[0].name}_{options[0].aggregation.value.lower()}, "
        f"{options[1].aggregation.value}(name_1) AS "
        f"{options[1].name}_{options[1].aggregation.value.lower()}"
    )

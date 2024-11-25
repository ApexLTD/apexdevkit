from faker import Faker

from apexdevkit.query.generator import MsSqlSourceGenerator
from apexdevkit.testing.fake import FakeFilter, FakeNumericValue, FakeStringValue


def test_should_generate_filter() -> None:
    function = Faker().text()
    num = FakeNumericValue().entity()
    text = FakeStringValue().entity()
    filtering = FakeFilter(args=[num, text]).entity()

    assert (
        MsSqlSourceGenerator(function, filtering).generate()
        == f"FROM {function}({num.eval()},'{text.value}')"
    )


def test_should_generate_from() -> None:
    table = Faker().text()

    assert MsSqlSourceGenerator(table).generate() == f"FROM {table}"

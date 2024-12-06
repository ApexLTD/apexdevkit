import pytest

from apexdevkit.error import ForbiddenError
from apexdevkit.query import Sort
from apexdevkit.query.generator import MsSqlField, MsSqlOrderGenerator
from tests.query.approvals.extension import verify_sql


def test_order_ascending() -> None:
    fields = [MsSqlField("id")]
    ordering = [Sort("id", is_descending=False)]

    generator = MsSqlOrderGenerator(ordering, fields)

    verify_sql(generator.generate())


def test_order_descending() -> None:
    fields = [MsSqlField("id")]
    ordering = [Sort("id", is_descending=True)]

    generator = MsSqlOrderGenerator(ordering, fields)

    verify_sql(generator.generate())


def test_order_with_alias() -> None:
    fields = [MsSqlField("id", alias="item_id")]
    ordering = [Sort("id", is_descending=False)]

    generator = MsSqlOrderGenerator(ordering, fields)

    verify_sql(generator.generate())


def test_should_order_with_multiple_fields() -> None:
    fields = [MsSqlField("id", alias="item_id"), MsSqlField("name")]
    ordering = [Sort("id", is_descending=True), Sort("name", is_descending=False)]

    generator = MsSqlOrderGenerator(ordering, fields)

    verify_sql(generator.generate())


def test_should_not_accept_unknown_field() -> None:
    fields = [MsSqlField("name")]
    generator = MsSqlOrderGenerator([Sort("id", is_descending=True)], fields)

    with pytest.raises(ForbiddenError) as cm:
        generator.generate()

    assert cm.value.message == "Invalid field name: id"

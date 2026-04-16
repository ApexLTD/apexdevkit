import pytest

from apexdevkit.error import ForbiddenError
from apexdevkit.query import Sort
from apexdevkit.query.generator import MsSqlField, MsSqlOrderGenerator
from tests.approvals.conftest import Approver


def test_order_ascending(approver: Approver) -> None:
    fields = [MsSqlField("id")]
    ordering = [Sort("id", is_descending=False)]

    generator = MsSqlOrderGenerator(ordering, fields)

    approver.verify_sql("ascending", generator.generate())


def test_order_descending(approver: Approver) -> None:
    fields = [MsSqlField("id")]
    ordering = [Sort("id", is_descending=True)]

    generator = MsSqlOrderGenerator(ordering, fields)

    approver.verify_sql("descending", generator.generate())


def test_order_with_alias(approver: Approver) -> None:
    fields = [MsSqlField("id", alias="item_id")]
    ordering = [Sort("item_id", is_descending=False)]

    generator = MsSqlOrderGenerator(ordering, fields)

    approver.verify_sql("with_alias", generator.generate())


def test_should_order_with_multiple_fields(approver: Approver) -> None:
    fields = [MsSqlField("id", alias="item_id"), MsSqlField("name")]
    ordering = [Sort("item_id", is_descending=True), Sort("name", is_descending=False)]

    generator = MsSqlOrderGenerator(ordering, fields)

    approver.verify_sql("with_multiple_fields", generator.generate())


def test_should_not_accept_unknown_field() -> None:
    fields = [MsSqlField("name")]
    generator = MsSqlOrderGenerator([Sort("id", is_descending=True)], fields)

    with pytest.raises(ForbiddenError) as cm:
        generator.generate()

    assert cm.value.message == "Invalid field name: id"

import pytest
from pytest_apex import ApprovalCase

from apexdevkit.error import ForbiddenError
from apexdevkit.query import Sort
from apexdevkit.query.generator import MsSqlField, MsSqlOrderGenerator


def test_ascending(approve: ApprovalCase) -> None:
    fields = [MsSqlField("id")]
    ordering = [Sort("id", is_descending=False)]

    generator = MsSqlOrderGenerator(ordering, fields)

    approve.sql().compact(generator.generate())


def test_descending(approve: ApprovalCase) -> None:
    fields = [MsSqlField("id")]
    ordering = [Sort("id", is_descending=True)]

    generator = MsSqlOrderGenerator(ordering, fields)

    approve.sql().compact(generator.generate())


def test_with_alias(approve: ApprovalCase) -> None:
    fields = [MsSqlField("id", alias="item_id")]
    ordering = [Sort("item_id", is_descending=False)]

    generator = MsSqlOrderGenerator(ordering, fields)

    approve.sql().compact(generator.generate())


def test_with_multiple_fields(approve: ApprovalCase) -> None:
    fields = [MsSqlField("id", alias="item_id"), MsSqlField("name")]
    ordering = [Sort("item_id", is_descending=True), Sort("name", is_descending=False)]

    generator = MsSqlOrderGenerator(ordering, fields)

    approve.sql().compact(generator.generate())


def test_should_reject_unknown_field() -> None:
    fields = [MsSqlField("name")]
    generator = MsSqlOrderGenerator([Sort("id", is_descending=True)], fields)

    with pytest.raises(ForbiddenError) as cm:
        generator.generate()

    assert cm.value.message == "Invalid field name: id"

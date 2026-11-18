from pytest_apex import ApprovalCase

from apexdevkit.query.generator import MsSqlField, MsSqlSelectionGenerator


def test_without_field_alias(approve: ApprovalCase) -> None:
    fields = [MsSqlField("id")]

    generator = MsSqlSelectionGenerator(fields)

    approve.sql().compact(generator.generate())


def test_with_field_alias(approve: ApprovalCase) -> None:
    fields = [MsSqlField("item_id", alias="id")]

    generator = MsSqlSelectionGenerator(fields)

    approve.sql().compact(generator.generate())


def test_with_multiple_fields(approve: ApprovalCase) -> None:
    fields = [MsSqlField("item_id", alias="id"), MsSqlField("name")]

    generator = MsSqlSelectionGenerator(fields)

    approve.sql().compact(generator.generate())

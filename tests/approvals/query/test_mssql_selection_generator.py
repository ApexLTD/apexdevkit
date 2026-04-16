from apexdevkit.query.generator import MsSqlField, MsSqlSelectionGenerator
from tests.approvals.conftest import Approver


def test_select_without_field_alias(approver: Approver) -> None:
    fields = [MsSqlField("id")]

    generator = MsSqlSelectionGenerator(fields)

    approver.verify_sql("without_field_alias", generator.generate())


def test_select_with_field_alias(approver: Approver) -> None:
    fields = [MsSqlField("item_id", alias="id")]

    generator = MsSqlSelectionGenerator(fields)

    approver.verify_sql("with_field_alias", generator.generate())


def test_select_with_multiple_fields(approver: Approver) -> None:
    fields = [MsSqlField("item_id", alias="id"), MsSqlField("name")]

    generator = MsSqlSelectionGenerator(fields)

    approver.verify_sql("with_multiple_fields", generator.generate())

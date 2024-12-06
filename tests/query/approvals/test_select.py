from apexdevkit.query.generator import MsSqlSelectionGenerator, MsSqlField
from tests.query.approvals.extension import verify_sql


def test_select_without_field_alias() -> None:
    fields = [MsSqlField("id")]

    verify_sql(MsSqlSelectionGenerator(fields).generate())


def test_select_with_field_alias() -> None:
    fields = [MsSqlField("item_id", alias="id")]

    verify_sql(MsSqlSelectionGenerator(fields).generate())


def test_select_with_multiple_fields() -> None:
    fields = [MsSqlField("item_id", alias="id"), MsSqlField("name")]

    verify_sql(MsSqlSelectionGenerator(fields).generate())

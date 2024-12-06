from apexdevkit.query.generator import MsSqlField, MsSqlSelectionGenerator


def test_should_generate_selection() -> None:
    fields = [
        MsSqlField("field", alias="test_field"),
        MsSqlField("field_2", alias="test_field_2"),
    ]

    result = MsSqlSelectionGenerator(fields).generate()

    assert result == "SELECT [field] AS [test_field], [field_2] AS [test_field_2]"

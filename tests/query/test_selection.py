from apexdevkit.query.generator import MsSqlSelectionGenerator


def test_should_generate_selection() -> None:
    fields = {
        "test_field": "field",
        "test_field_2": "field_2",
    }

    result = MsSqlSelectionGenerator(fields).generate()

    assert result == "SELECT [field] AS [test_field], [field_2] AS [test_field_2]"

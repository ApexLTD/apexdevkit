from apexdevkit.query.generator import MsSqlUserGenerator


def test_should_generate_user() -> None:
    assert MsSqlUserGenerator("phoenix").generate() == "EXECUTE AS USER = 'phoenix'"

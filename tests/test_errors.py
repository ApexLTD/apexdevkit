from apexdevkit.error import DoesNotExistError, ExistsError


def test_default_exists_error() -> None:
    assert ExistsError().id == "unknown"


def test_default_does_not_exist_error() -> None:
    assert DoesNotExistError().id == "unknown"

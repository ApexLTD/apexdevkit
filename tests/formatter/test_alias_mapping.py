import pytest

from apexdevkit.formatter import AliasMapping


@pytest.fixture
def alias() -> AliasMapping:
    return AliasMapping.parse(id="ID", name="Name")


def test_should_translate_individual_keys(alias: AliasMapping) -> None:
    assert alias.value_of("id") == "ID"
    assert alias.value_of("name") == "Name"


def test_should_reverse_translate_individual_keys(alias: AliasMapping) -> None:
    assert alias.reverse().value_of("ID") == "id"
    assert alias.reverse().value_of("Name") == "name"


def test_should_preserve_key_without_alias(alias: AliasMapping) -> None:
    assert alias.value_of("amount") == "amount"
    assert alias.reverse().value_of("amount") == "amount"


def test_should_translate_object(alias: AliasMapping) -> None:
    source = {
        "id": "1",
        "name": "orion",
        "amount": 10,
    }

    assert alias.translate(source) == {
        "ID": "1",
        "Name": "orion",
        "amount": 10,
    }


def test_should_reverse_translate_object(alias: AliasMapping) -> None:
    source = {
        "ID": "1",
        "Name": "orion",
        "amount": 10,
    }

    assert alias.reverse().translate(source) == {
        "id": "1",
        "name": "orion",
        "amount": 10,
    }

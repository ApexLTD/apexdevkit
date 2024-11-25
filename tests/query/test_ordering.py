from apexdevkit.query.generator import MsSqlOrderGenerator
from apexdevkit.testing.fake import FakeSort


def test_should_order_by_default_field() -> None:
    assert MsSqlOrderGenerator([], {}).generate() == ""


def test_should_order_ascending() -> None:
    sort = FakeSort(is_descending=False).entity()
    translation = {sort.name: "name"}

    assert MsSqlOrderGenerator([sort], translation).generate() == "ORDER BY name"


def test_should_order_descending() -> None:
    sort = FakeSort(is_descending=True).entity()
    translation = {sort.name: "name"}

    assert MsSqlOrderGenerator([sort], translation).generate() == "ORDER BY name DESC"


def test_should_order_multiple() -> None:
    asc = FakeSort(is_descending=False).entity()
    desc = FakeSort(is_descending=True).entity()
    translation = {asc.name: "asc", desc.name: "desc"}

    assert (
        MsSqlOrderGenerator([asc, desc], translation).generate()
        == "ORDER BY asc, desc DESC"
    )

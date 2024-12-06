from apexdevkit.query.generator import MsSqlField, MsSqlOrderGenerator
from apexdevkit.testing.fake import FakeSort


def test_should_order_by_default_field() -> None:
    fields = []

    generator = MsSqlOrderGenerator([], fields)

    assert generator.generate() == ""


def test_should_order_ascending() -> None:
    sort = FakeSort(is_descending=False).entity()
    fields = [MsSqlField(sort.name, alias="name")]
    generator = MsSqlOrderGenerator([sort], fields)

    assert generator.generate() == "ORDER BY name"


def test_should_order_descending() -> None:
    sort = FakeSort(is_descending=True).entity()
    fields = [MsSqlField(sort.name, alias="name")]
    generator = MsSqlOrderGenerator([sort], fields)

    assert generator.generate() == "ORDER BY name DESC"


def test_should_order_multiple() -> None:
    asc = FakeSort(is_descending=False).entity()
    desc = FakeSort(is_descending=True).entity()
    fields = [MsSqlField(asc.name, alias="asc"), MsSqlField(desc.name, alias="desc")]
    generator = MsSqlOrderGenerator([asc, desc], fields)

    assert generator.generate() == "ORDER BY asc, desc DESC"

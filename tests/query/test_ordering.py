from apexdevkit.query.generator import MsSqlField, MsSqlOrderGenerator
from apexdevkit.testing.fake import FakeSort


def test_should_order_by_default_field() -> None:
    assert MsSqlOrderGenerator(ordering=[], fields=[]).generate() == ""


def test_should_order_ascending() -> None:
    sort = FakeSort(is_descending=False).entity()
    fields = [MsSqlField("name", alias=sort.name)]
    generator = MsSqlOrderGenerator([sort], fields)

    assert generator.generate() == "ORDER BY name"


def test_should_order_descending() -> None:
    sort = FakeSort(is_descending=True).entity()
    fields = [MsSqlField("name", alias=sort.name)]
    generator = MsSqlOrderGenerator([sort], fields)

    assert generator.generate() == "ORDER BY name DESC"


def test_should_order_multiple() -> None:
    asc = FakeSort(is_descending=False).entity()
    desc = FakeSort(is_descending=True).entity()
    fields = [MsSqlField("asc", alias=asc.name), MsSqlField("desc", alias=desc.name)]
    generator = MsSqlOrderGenerator([asc, desc], fields)

    assert generator.generate() == "ORDER BY asc, desc DESC"


def test_should_order_without_alias() -> None:
    sort = FakeSort(is_descending=False).entity()
    fields = [MsSqlField(sort.name)]
    generator = MsSqlOrderGenerator([sort], fields)

    assert generator.generate() == f"ORDER BY {sort.name}"


def test_should_order_with_the_same_alias_and_name() -> None:
    sort = FakeSort(is_descending=False).entity()
    fields = [MsSqlField(sort.name, sort.name)]
    generator = MsSqlOrderGenerator([sort], fields)

    assert generator.generate() == f"ORDER BY {sort.name}"

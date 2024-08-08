from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterator, Protocol
from unittest.mock import ANY

import pytest
from faker import Faker

from apexdevkit.error import DoesNotExistError
from apexdevkit.repository import Database, DatabaseCommand
from apexdevkit.repository.sqlite import SqliteRepository, UnknownError
from apexdevkit.testing import FakeConnector


@dataclass
class FakeTable:
    def setup(self) -> DatabaseCommand:
        return DatabaseCommand("Command: Create")

    def insert(self, item: Any) -> DatabaseCommand:
        return DatabaseCommand("Command: Insert").with_data(self.dump(item))

    def select(self, item_id: str) -> DatabaseCommand:
        return DatabaseCommand("Command: Select").with_data({"item_id": item_id})

    def select_all(self) -> DatabaseCommand:
        return DatabaseCommand("Command: Select All")

    def count_all(self) -> DatabaseCommand:
        return DatabaseCommand("Command: Count All")

    def update(self, item: _Item) -> DatabaseCommand:
        return DatabaseCommand("Command: Update").with_data(self.dump(item))

    def delete(self, item_id: str) -> DatabaseCommand:
        return DatabaseCommand("Command: Delete").with_data({"item_id": item_id})

    def delete_all(self) -> DatabaseCommand:
        return DatabaseCommand("Command: Delete All")

    def load(self, data: Any) -> Any:
        return Loaded(data)

    def dump(self, data: Any) -> dict[str, Any]:
        return {"dumped": data}


@dataclass
class NonExisting:
    id: str = "new_id"
    external_id: str = "new_external_id"


@dataclass
class Existing:
    id: str = "existing_id"
    external_id: str = "existing_external_id"

    def __iter__(self) -> Iterator[Any]:
        yield from {"id": self.id, "external_id": self.external_id}.items()


@dataclass
class Loaded:
    value: Any

    id: str = "id"
    external_id: str = "external_id"


class _Item(Protocol):
    id: str
    external_id: str


def test_should_fail_to_count(faker: Faker) -> None:
    expected = faker.pydict()
    connector = FakeConnector().with_result(expected)

    repository = SqliteRepository[_Item](table=FakeTable(), db=Database(connector))

    with pytest.raises(UnknownError) as cm:
        len(repository)

    assert cm.value.raw == expected


def test_should_perform_count_query(faker: Faker) -> None:
    connector = FakeConnector().with_result({"n_items": faker.pyint()})
    repository = SqliteRepository[_Item](table=FakeTable(), db=Database(connector))

    len(repository)

    connector.assert_contains(FakeTable().count_all())


def test_should_count(faker: Faker) -> None:
    expected = faker.pyint()
    connector = FakeConnector().with_result({"n_items": expected})

    repository = SqliteRepository[_Item](table=FakeTable(), db=Database(connector))

    actual = len(repository)

    assert actual == expected


def test_should_perform_create_command() -> None:
    connector = FakeConnector().with_result({"id": ANY, "code": 0})
    repository = SqliteRepository[_Item](table=FakeTable(), db=Database(connector))

    repository.create(NonExisting())

    connector.assert_contains(FakeTable().insert(NonExisting()))


def test_should_not_read_unknown() -> None:
    connector = FakeConnector().with_result({})
    repository = SqliteRepository[_Item](table=FakeTable(), db=Database(connector))

    with pytest.raises(DoesNotExistError):
        repository.read(NonExisting().id)


def test_should_perform_read_query() -> None:
    connector = FakeConnector().with_result(Existing())
    repository = SqliteRepository[_Item](table=FakeTable(), db=Database(connector))

    repository.read(Existing().id)

    connector.assert_contains(FakeTable().select(Existing().id))


def test_should_read() -> None:
    connector = FakeConnector().with_result(Existing())
    repository = SqliteRepository[_Item](table=FakeTable(), db=Database(connector))

    actual = repository.read(Existing().id)

    assert actual == Loaded(dict(Existing()))


def test_should_perform_delete_all_command() -> None:
    connector = FakeConnector().with_result(Existing())
    repository = SqliteRepository[_Item](table=FakeTable(), db=Database(connector))

    repository.delete_all()

    connector.assert_contains(FakeTable().delete_all())


def test_should_perform_delete_command() -> None:
    connector = FakeConnector()
    repository = SqliteRepository[_Item](table=FakeTable(), db=Database(connector))

    repository.delete(Existing().id)

    connector.assert_contains(FakeTable().delete(Existing().id))


def test_should_not_list_anything_when_none_exist() -> None:
    connector = FakeConnector().with_result([])
    repository = SqliteRepository[_Item](table=FakeTable(), db=Database(connector))

    assert [item for item in repository] == []


def test_should_perform_select_all_query() -> None:
    connector = FakeConnector().with_result([])
    repository = SqliteRepository[_Item](table=FakeTable(), db=Database(connector))

    _ = [item for item in repository]

    connector.assert_contains(FakeTable().select_all())


def test_should_list_all() -> None:
    connector = FakeConnector().with_result([Existing(str(i)) for i in range(10)])

    repository = SqliteRepository[_Item](table=FakeTable(), db=Database(connector))

    assert [Loaded(Existing(str(i))) for i in range(10)] == [i for i in repository]


def test_should_perform_update_query() -> None:
    connector = FakeConnector().with_result(Existing())
    repository = SqliteRepository[_Item](table=FakeTable(), db=Database(connector))

    repository.update(Existing())

    connector.assert_contains(FakeTable().update(Existing()))

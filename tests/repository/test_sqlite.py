from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from pytest import fixture, raises

from apexdevkit.error import DoesNotExistError, ExistsError
from apexdevkit.formatter import DataclassFormatter
from apexdevkit.repository import Database, DatabaseCommand, Repository
from apexdevkit.repository.connector import SqliteInMemoryConnector
from apexdevkit.repository.sqlite import SqliteRepository, SqlTable


@dataclass
class _Item:
    id: str
    external_id: str


class FakeTable(SqlTable[_Item]):
    def setup(self) -> DatabaseCommand:
        return DatabaseCommand("""
            CREATE TABLE IF NOT EXISTS ITEM (
                id              TEXT        NOT NULL    PRIMARY KEY,
                external_id     TEXT        NOT NULL,

                UNIQUE(id)
            );
        """)

    def count_all(self) -> DatabaseCommand:
        return DatabaseCommand("SELECT COUNT(*) as n_items FROM ITEM;")

    def select_all(self) -> DatabaseCommand:
        return DatabaseCommand("SELECT * FROM ITEM;")

    def select(self, item_id: str) -> DatabaseCommand:
        return DatabaseCommand("SELECT * FROM ITEM WHERE id=:id").with_data(id=item_id)

    def select_duplicate(self, item: _Item) -> DatabaseCommand:
        return self.select(item.id)

    def insert(self, item: _Item) -> DatabaseCommand:
        return DatabaseCommand("""
            INSERT INTO ITEM (id, external_id) VALUES (:id, :external_id)
            RETURNING id, external_id;
        """).with_data(DataclassFormatter[_Item](_Item).dump(item))

    def update(self, item: _Item) -> DatabaseCommand:
        return DatabaseCommand("""
            UPDATE ITEM SET id=:id, external_id=:external_id WHERE id=:id;
        """).with_data(DataclassFormatter[_Item](_Item).dump(item))

    def delete(self, item_id: str) -> DatabaseCommand:
        return DatabaseCommand("DELETE FROM ITEM WHERE id=:id").with_data(id=item_id)

    def delete_all(self) -> DatabaseCommand:
        return DatabaseCommand("DELETE FROM ITEM")

    def load(self, data: dict[str, Any]) -> _Item:
        return DataclassFormatter[_Item](_Item).load(data)

    def duplicate(self, item: _Item) -> ExistsError:
        return ExistsError(item).with_duplicate(
            lambda i: f"_Item with id<{i.id}> already exists."
        )


@fixture
def repository() -> Repository[str, _Item]:
    db = Database(SqliteInMemoryConnector())
    db.execute(FakeTable().setup()).fetch_none()

    return SqliteRepository[str, _Item](table=FakeTable(), db=db)


def test_should_list_nothing_when_empty(repository: Repository[str, _Item]) -> None:
    assert len(repository) == 0
    assert list(repository) == []


def test_should_not_read_unknown(repository: Repository[str, _Item]) -> None:
    with raises(DoesNotExistError):
        repository.read(str(uuid4()))


def test_should_create(repository: Repository[str, _Item]) -> None:
    item = _Item(id=str(uuid4()), external_id=str(uuid4()))

    assert repository.create(item) == item


def test_should_not_duplicate_on_create(repository: Repository[str, _Item]) -> None:
    item = _Item(id=str(uuid4()), external_id=str(uuid4()))
    repository.create(item)

    with raises(ExistsError, match=f"_Item with id<{item.id}> already exists."):
        repository.create(item)


def test_should_create_many(repository: Repository[str, _Item]) -> None:
    items = [
        _Item(id=str(uuid4()), external_id=str(uuid4())),
        _Item(id=str(uuid4()), external_id=str(uuid4())),
    ]

    assert repository.create_many(items) == items


def test_should_not_duplicate_on_create_many(
    repository: Repository[str, _Item],
) -> None:
    items = [
        _Item(id=str(uuid4()), external_id=str(uuid4())),
        _Item(id=str(uuid4()), external_id=str(uuid4())),
    ]
    repository.create(items[1])

    with raises(ExistsError, match=f"_Item with id<{items[1].id}> already exists."):
        repository.create_many(items)


def test_should_persist(repository: Repository[str, _Item]) -> None:
    item = _Item(id=str(uuid4()), external_id=str(uuid4()))
    repository.create(item)

    assert len(repository) == 1
    assert repository.read(item.id) == item


def test_should_persist_many(repository: Repository[str, _Item]) -> None:
    items = [
        _Item(id=str(uuid4()), external_id=str(uuid4())),
        _Item(id=str(uuid4()), external_id=str(uuid4())),
    ]
    repository.create_many(items)

    assert len(repository) == 2
    assert list(repository) == items


def test_should_persist_update(repository: Repository[str, _Item]) -> None:
    old_item = _Item(id=str(uuid4()), external_id=str(uuid4()))
    repository.create(old_item)

    item = _Item(id=old_item.id, external_id=str(uuid4()))
    repository.update(item)

    assert repository.read(item.id) == item


def test_should_persist_update_many(repository: Repository[str, _Item]) -> None:
    old_items = [
        _Item(id=str(uuid4()), external_id=str(uuid4())),
        _Item(id=str(uuid4()), external_id=str(uuid4())),
    ]
    repository.create_many(old_items)

    items = [
        _Item(id=old_items[0].id, external_id=str(uuid4())),
        _Item(id=old_items[1].id, external_id=str(uuid4())),
    ]
    repository.update_many(items)

    assert list(repository) == items


def test_should_persist_delete(repository: Repository[str, _Item]) -> None:
    items = [
        _Item(id=str(uuid4()), external_id=str(uuid4())),
        _Item(id=str(uuid4()), external_id=str(uuid4())),
    ]
    repository.create_many(items)

    repository.delete(items[1].id)

    assert list(repository) == [items[0]]


def test_should_persist_delete_all(repository: SqliteRepository[str, _Item]) -> None:
    items = [
        _Item(id=str(uuid4()), external_id=str(uuid4())),
        _Item(id=str(uuid4()), external_id=str(uuid4())),
    ]
    repository.create_many(items)

    repository.delete_all()

    assert list(repository) == []

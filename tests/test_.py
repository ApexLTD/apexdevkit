from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from pytest import fixture, raises

from apexdevkit.error import DoesNotExistError, ExistsError
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

    def insert(self, item: _Item) -> DatabaseCommand:
        return DatabaseCommand("""
            INSERT INTO ITEM (id, external_id) VALUES (:id, :external_id)
            RETURNING id, external_id;
        """).with_data({"id": item.id, "external_id": item.external_id})

    def load(self, data: dict[str, Any]) -> _Item:
        return _Item(data["id"], data["external_id"])


@fixture
def repository() -> Repository[str, _Item]:
    db = Database(SqliteInMemoryConnector())
    db.execute(FakeTable().setup()).fetch_none()

    return SqliteRepository[_Item](
        table=FakeTable(),
        db=db,
        duplicate_criteria=lambda item: f"_Item with id<{item.id}> already exists.",
    )


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

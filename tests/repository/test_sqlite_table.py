from dataclasses import dataclass
from uuid import uuid4

from _pytest.fixtures import fixture
from _pytest.python_api import raises

from apexdevkit.error import DoesNotExistError, ExistsError
from apexdevkit.formatter import DataclassFormatter
from apexdevkit.repository import Database, DatabaseCommand
from apexdevkit.repository.connector import SqliteInMemoryConnector
from apexdevkit.repository.sqlite import SqliteRepository, SqliteTableBuilder


@dataclass(frozen=True)
class _Item:
    id: str

    name: str
    count: int


def setup() -> DatabaseCommand:
    return DatabaseCommand("""
        CREATE TABLE IF NOT EXISTS ITEM (
            id              TEXT        NOT NULL    PRIMARY KEY,
            name            TEXT        NOT NULL,
            count           INT         NOT NULL,

            UNIQUE(id)
        );
    """)


@fixture
def item() -> _Item:
    return _Item(str(uuid4()), "item", 1)


@fixture
def repository() -> SqliteRepository[_Item]:
    db = Database(SqliteInMemoryConnector())
    db.execute(setup()).fetch_none()

    return SqliteRepository[_Item](
        table=SqliteTableBuilder[_Item]()
        .with_name("item")
        .with_formatter(DataclassFormatter(_Item))
        .with_fields(["id", "name", "count"])
        .with_id("id")
        .with_composite_key(["id"])
        .build(),
        db=db,
    )


def test_should_list_nothing_when_empty(repository: SqliteRepository[_Item]) -> None:
    assert len(repository) == 0
    assert list(repository) == []


def test_should_not_read_unknown(repository: SqliteRepository[_Item]) -> None:
    with raises(DoesNotExistError):
        repository.read(str(uuid4()))


def test_should_create(repository: SqliteRepository[_Item], item: _Item) -> None:
    assert repository.create(item) == item


def test_should_not_duplicate_on_create(
    repository: SqliteRepository[_Item], item: _Item
) -> None:
    repository.create(item)

    with raises(ExistsError, match=f"id<{item.id}>"):
        repository.create(item)


def test_should_persist(repository: SqliteRepository[_Item], item: _Item) -> None:
    repository.create(item)

    assert len(repository) == 1
    assert repository.read(item.id) == item


def test_should_persist_update(
    repository: SqliteRepository[_Item], item: _Item
) -> None:
    old_item = _Item(id=item.id, name="new", count=0)
    repository.create(old_item)

    repository.update(item)

    assert repository.read(item.id) == item


def test_should_persist_delete(
    repository: SqliteRepository[_Item], item: _Item
) -> None:
    repository.create(item)

    repository.delete(item.id)

    assert list(repository) == []


def test_should_persist_delete_all(
    repository: SqliteRepository[_Item], item: _Item
) -> None:
    repository.create(item)

    repository.delete_all()

    assert list(repository) == []
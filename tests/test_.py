from dataclasses import dataclass
from uuid import uuid4

from pytest import fixture, raises

from apexdevkit.error import DoesNotExistError
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


@fixture
def repository() -> Repository[str, _Item]:
    db = Database(SqliteInMemoryConnector())
    db.execute(FakeTable().setup()).fetch_none()

    return SqliteRepository[_Item](table=FakeTable(), db=db)


def test_should_list_nothing_when_empty(repository: Repository[str, _Item]) -> None:
    assert len(repository) == 0
    assert list(repository) == []


def test_should_not_read_unknown(repository: Repository[str, _Item]) -> None:
    with raises(DoesNotExistError):
        repository.read(str(uuid4()))


def test_should_create(repository: Repository[str, _Item]) -> None:
    item = _Item(id=str(uuid4()), external_id=str(uuid4()))

    assert repository.create(item) == item

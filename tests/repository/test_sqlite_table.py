from uuid import uuid4

from _pytest.fixtures import fixture
from _pytest.raises import raises

from apexdevkit.error import DoesNotExistError, ExistsError
from apexdevkit.formatter import DataclassFormatter
from apexdevkit.repository import Database, DatabaseCommand
from apexdevkit.repository.sql import SqlFieldBuilder
from apexdevkit.repository.sql.connector import SqliteInMemoryConnector
from apexdevkit.repository.sql.sqlite import (
    SqliteRepository,
    SqliteTableBuilder,
)
from tests.repository.data import SqliteTableItem


def setup() -> DatabaseCommand:
    return DatabaseCommand("""
        CREATE TABLE IF NOT EXISTS ITEM (
            id              TEXT        NOT NULL    PRIMARY KEY,
            name            TEXT        NOT NULL,
            count           INT         NOT NULL,
            parent          INT         NOT NULL,
            fixed           INT         NOT NULL,

            UNIQUE(id)
        );
    """)


@fixture
def item() -> SqliteTableItem:
    return SqliteTableItem(id=str(uuid4()), name="item", count=1)


@fixture
def item_with_parent(item: SqliteTableItem) -> SqliteTableItem:
    return SqliteTableItem(id=item.id, name="item", count=1, parent=0)


@fixture
def repository() -> SqliteRepository[SqliteTableItem]:
    db = Database(SqliteInMemoryConnector())
    db.execute(setup()).fetch_none()

    return SqliteRepository[SqliteTableItem](
        table=SqliteTableBuilder[SqliteTableItem]()
        .with_name("item")
        .with_formatter(DataclassFormatter(SqliteTableItem))
        .with_fields(
            [
                SqlFieldBuilder().with_name("id").as_id().as_composite().build(),
                SqlFieldBuilder().with_name("name").as_selectable().build(),
                SqlFieldBuilder().with_name("count").build(),
                SqlFieldBuilder().with_name("parent").as_parent(0).build(),
                SqlFieldBuilder().with_name("fixed").as_fixed(1).build(),
            ]
        )
        .build(),
        db=db,
    )


def test_should_list_nothing_when_empty(
    repository: SqliteRepository[SqliteTableItem],
) -> None:
    assert len(repository) == 0
    assert list(repository) == []


def test_should_not_read_unknown(repository: SqliteRepository[SqliteTableItem]) -> None:
    with raises(DoesNotExistError):
        repository.read(str(uuid4()))


def test_should_create(
    repository: SqliteRepository[SqliteTableItem],
    item: SqliteTableItem,
    item_with_parent: SqliteTableItem,
) -> None:
    assert repository.create(item) == item_with_parent


def test_should_not_duplicate_on_create(
    repository: SqliteRepository[SqliteTableItem], item: SqliteTableItem
) -> None:
    repository.create(item)

    with raises(ExistsError, match=f"id<{item.id}>"):
        repository.create(item)


def test_should_persist(
    repository: SqliteRepository[SqliteTableItem],
    item: SqliteTableItem,
    item_with_parent: SqliteTableItem,
) -> None:
    repository.create(item)

    assert len(repository) == 1
    assert repository.read(item.name) == item_with_parent


def test_should_persist_update(
    repository: SqliteRepository[SqliteTableItem],
    item: SqliteTableItem,
    item_with_parent: SqliteTableItem,
) -> None:
    old_item = SqliteTableItem(id=item.id, name="new", count=0)
    repository.create(old_item)

    repository.update(item)

    assert repository.read(item.name) == item_with_parent


def test_should_persist_delete(
    repository: SqliteRepository[SqliteTableItem], item: SqliteTableItem
) -> None:
    repository.create(item)

    repository.delete(item.name)

    assert list(repository) == []


def test_should_persist_delete_all(
    repository: SqliteRepository[SqliteTableItem], item: SqliteTableItem
) -> None:
    repository.create(item)

    repository.delete_all()

    assert list(repository) == []

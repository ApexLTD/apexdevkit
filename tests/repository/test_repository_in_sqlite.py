from uuid import uuid4

import pytest

from apexdevkit.error import DoesNotExistError, ExistsError
from apexdevkit.formatter import DataclassFormatter
from apexdevkit.repository import Database, DatabaseCommand, Repository
from apexdevkit.repository.sql import SqlFieldBuilder
from apexdevkit.repository.sql.connector import SqliteInMemoryConnector
from apexdevkit.repository.sql.sqlite import (
    SqliteRepository,
    SqliteTableBuilder,
)
from tests.repository.data import SqliteItem


@pytest.fixture
def repository() -> SqliteRepository[SqliteItem]:
    db = Database(SqliteInMemoryConnector())
    db.execute(
        DatabaseCommand("""
            CREATE TABLE IF NOT EXISTS ITEM (
                id              TEXT        NOT NULL    PRIMARY KEY,
                external_id     TEXT        NOT NULL,

                UNIQUE(id)
            );
        """)
    ).fetch_none()

    return SqliteRepository(
        db=db,
        table=(
            SqliteTableBuilder[SqliteItem]()
            .with_name("ITEM")
            .with_formatter(DataclassFormatter(SqliteItem))
            .with_fields(
                [
                    SqlFieldBuilder().with_name("id").as_id().build(),
                    SqlFieldBuilder().with_name("external_id").build(),
                ]
            )
            .build()
        ),
    )


def test_should_list_nothing_when_empty(repository: Repository[SqliteItem]) -> None:
    assert len(repository) == 0
    assert list(repository) == []


def test_should_not_read_unknown(repository: Repository[SqliteItem]) -> None:
    with pytest.raises(DoesNotExistError):
        repository.read(str(uuid4()))


def test_should_create(repository: Repository[SqliteItem]) -> None:
    item = SqliteItem(id=str(uuid4()), external_id=str(uuid4()))

    assert repository.create(item) == item


def test_should_not_duplicate_on_create(repository: Repository[SqliteItem]) -> None:
    item = SqliteItem(id=str(uuid4()), external_id=str(uuid4()))
    repository.create(item)

    with pytest.raises(ExistsError, match=f"id<{item.id}>"):
        repository.create(item)


def test_should_persist(repository: Repository[SqliteItem]) -> None:
    item = SqliteItem(id=str(uuid4()), external_id=str(uuid4()))
    repository.create(item)

    assert len(repository) == 1
    assert repository.read(item.id) == item


def test_should_persist_update(repository: Repository[SqliteItem]) -> None:
    old_item = SqliteItem(id=str(uuid4()), external_id=str(uuid4()))
    repository.create(old_item)

    item = SqliteItem(id=old_item.id, external_id=str(uuid4()))
    repository.update(item)

    assert repository.read(item.id) == item


def test_should_persist_delete(repository: Repository[SqliteItem]) -> None:
    item = SqliteItem(id=str(uuid4()), external_id=str(uuid4()))
    repository.create(item)

    repository.delete(item.id)

    assert list(repository) == []

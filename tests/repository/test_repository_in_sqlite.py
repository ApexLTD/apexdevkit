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
from tests.repository.data import AppleItem


@pytest.fixture
def repository() -> SqliteRepository[AppleItem]:
    db = Database(SqliteInMemoryConnector())
    db.execute(
        DatabaseCommand(
            """
            CREATE TABLE IF NOT EXISTS ITEM (
                id              TEXT        NOT NULL    PRIMARY KEY,
                color     TEXT        NOT NULL,

                UNIQUE(id)
            );
            """
        )
    ).fetch_none()

    return SqliteRepository(
        db=db,
        table=(
            SqliteTableBuilder[AppleItem]()
            .with_name("ITEM")
            .with_formatter(DataclassFormatter(AppleItem))
            .with_fields(
                [
                    SqlFieldBuilder().with_name("id").as_id().build(),
                    SqlFieldBuilder().with_name("color").build(),
                ]
            )
            .build()
        ),
    )


def test_should_list_nothing_when_empty(repository: Repository[AppleItem]) -> None:
    assert len(repository) == 0
    assert list(repository) == []


def test_should_not_read_unknown(repository: Repository[AppleItem]) -> None:
    with pytest.raises(DoesNotExistError):
        repository.read(str(uuid4()))


def test_should_create(repository: Repository[AppleItem]) -> None:
    item = AppleItem(id=str(uuid4()), color=str(uuid4()))

    assert repository.create(item) == item


def test_should_not_duplicate_on_create(repository: Repository[AppleItem]) -> None:
    item = AppleItem(id=str(uuid4()), color=str(uuid4()))
    repository.create(item)

    with pytest.raises(ExistsError, match=f"id<{item.id}>"):
        repository.create(item)


def test_should_persist(repository: Repository[AppleItem]) -> None:
    item = AppleItem(id=str(uuid4()), color=str(uuid4()))
    repository.create(item)

    assert len(repository) == 1
    assert repository.read(item.id) == item


def test_should_persist_update(repository: Repository[AppleItem]) -> None:
    old_item = AppleItem(id=str(uuid4()), color=str(uuid4()))
    repository.create(old_item)

    item = AppleItem(id=old_item.id, color=str(uuid4()))
    repository.update(item)

    assert repository.read(item.id) == item


def test_should_persist_delete(repository: Repository[AppleItem]) -> None:
    item = AppleItem(id=str(uuid4()), color=str(uuid4()))
    repository.create(item)

    repository.delete(item.id)

    assert list(repository) == []

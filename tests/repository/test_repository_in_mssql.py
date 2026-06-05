from unittest.mock import MagicMock

import pytest
from pymssql.exceptions import DatabaseError

from apexdevkit.error import DoesNotExistError, ExistsError
from apexdevkit.formatter import DataclassFormatter
from apexdevkit.repository import Database, MsSqlRepository
from apexdevkit.repository.sql import SqlFieldBuilder
from apexdevkit.repository.sql.mssql import MsSqlTableBuilder, UnknownError
from tests.repository.data import AppleMsSqlItem

TABLE = (
    MsSqlTableBuilder[AppleMsSqlItem]()
    .with_schema("test")
    .with_table("apples")
    .with_formatter(DataclassFormatter(AppleMsSqlItem))
    .with_fields(
        [
            SqlFieldBuilder().with_name("id").as_id().build(),
            SqlFieldBuilder().with_name("color").build(),
        ]
    )
    .build()
)


@pytest.fixture
def apple() -> AppleMsSqlItem:
    return AppleMsSqlItem(color="red")


def test_should_retrieve_all(apple: AppleMsSqlItem) -> None:
    db = MagicMock(spec=Database)
    executor = MagicMock(spec=Database._CommandExecutor)
    db.execute.return_value = executor

    executor.fetch_all.return_value = [
        {
            "id": apple.id,
            "color": apple.color,
        }
    ]
    result = list(iter(MsSqlRepository[AppleMsSqlItem](db, TABLE)))

    db.execute.assert_called_once_with(TABLE.select_all())
    executor.fetch_all.assert_called_once()
    assert result == [apple]


def test_should_count_all() -> None:
    db = MagicMock(spec=Database)
    executor = MagicMock(spec=Database._CommandExecutor)
    db.execute.return_value = executor

    executor.fetch_one.return_value = {"n_items": 1}
    result = len(MsSqlRepository[AppleMsSqlItem](db, TABLE))

    db.execute.assert_called_once_with(TABLE.count_all())
    executor.fetch_one.assert_called_once()
    assert result == 1


def test_should_not_count_all() -> None:
    db = MagicMock(spec=Database)
    executor = MagicMock(spec=Database._CommandExecutor)
    db.execute.return_value = executor

    executor.fetch_one.return_value = {}
    with pytest.raises(UnknownError):
        len(MsSqlRepository[AppleMsSqlItem](db, TABLE))


def test_should_delete(apple: AppleMsSqlItem) -> None:
    db = MagicMock(spec=Database)
    executor = MagicMock(spec=Database._CommandExecutor)
    db.execute.return_value = executor

    MsSqlRepository[AppleMsSqlItem](db, TABLE).delete(apple.id)

    db.execute.assert_called_once_with(TABLE.delete(apple.id))
    executor.fetch_none.assert_called_once()


def test_should_delete_all() -> None:
    db = MagicMock(spec=Database)
    executor = MagicMock(spec=Database._CommandExecutor)
    db.execute.return_value = executor

    MsSqlRepository[AppleMsSqlItem](db, TABLE).delete_all()

    db.execute.assert_called_once_with(TABLE.delete_all())
    executor.fetch_none.assert_called_once()


def test_should_create(apple: AppleMsSqlItem) -> None:
    db = MagicMock(spec=Database)
    executor = MagicMock(spec=Database._CommandExecutor)
    db.execute.return_value = executor

    executor.fetch_one.return_value = {
        "id": apple.id,
        "color": apple.color,
    }

    result = MsSqlRepository[AppleMsSqlItem](db, TABLE).create(apple)

    db.execute.assert_called_once_with(TABLE.insert(apple))
    executor.fetch_one.assert_called_once()
    assert result == apple


def test_should_not_duplicate(apple: AppleMsSqlItem) -> None:
    db = MagicMock(spec=Database)
    executor = MagicMock(spec=Database._CommandExecutor)
    db.execute.return_value = executor

    db.execute.side_effect = DatabaseError(2627, b"duplication")

    with pytest.raises(ExistsError):
        MsSqlRepository[AppleMsSqlItem](db, TABLE).create(apple)


def test_should_not_create(apple: AppleMsSqlItem) -> None:
    db = MagicMock(spec=Database)
    executor = MagicMock(spec=Database._CommandExecutor)
    db.execute.return_value = executor

    db.execute.side_effect = DatabaseError(0, b"error")

    with pytest.raises(UnknownError):
        MsSqlRepository[AppleMsSqlItem](db, TABLE).create(apple)


def test_should_read(apple: AppleMsSqlItem) -> None:
    db = MagicMock(spec=Database)
    executor = MagicMock(spec=Database._CommandExecutor)
    db.execute.return_value = executor

    executor.fetch_one.return_value = {
        "id": apple.id,
        "color": apple.color,
    }

    result = MsSqlRepository[AppleMsSqlItem](db, TABLE).read(apple.id)

    db.execute.assert_called_once_with(TABLE.select(apple.id))
    executor.fetch_one.assert_called_once()
    assert result == apple


def test_should_not_read_unknown(apple: AppleMsSqlItem) -> None:
    db = MagicMock(spec=Database)
    executor = MagicMock(spec=Database._CommandExecutor)
    db.execute.return_value = executor

    executor.fetch_one.return_value = None

    with pytest.raises(DoesNotExistError):
        MsSqlRepository[AppleMsSqlItem](db, TABLE).read(apple.id)


def test_should_update(apple: AppleMsSqlItem) -> None:
    db = MagicMock(spec=Database)
    executor = MagicMock(spec=Database._CommandExecutor)
    db.execute.return_value = executor

    MsSqlRepository[AppleMsSqlItem](db, TABLE).update(apple)

    db.execute.assert_called_once_with(TABLE.update(apple))
    executor.fetch_none.assert_called_once()

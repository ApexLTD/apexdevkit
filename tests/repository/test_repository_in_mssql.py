from collections.abc import Mapping
from typing import Any
from unittest.mock import MagicMock

import pytest
from pymssql.exceptions import DatabaseError

from apexdevkit.error import DoesNotExistError, ExistsError
from apexdevkit.repository import Database, DatabaseCommand, MsSqlRepository
from apexdevkit.repository.sql.mssql import SqlTable, UnknownError
from tests.repository.data import AppleMsSqlItem


class AppleTable(SqlTable[AppleMsSqlItem]):
    def count_all(self) -> DatabaseCommand:
        return DatabaseCommand("SELECT COUNT(*) AS n_items FROM test.apples")

    def insert(self, apple: AppleMsSqlItem) -> DatabaseCommand:
        return DatabaseCommand("""
            INSERT INTO test.apples ([clr])
            OUTPUT (INSERTED.clr AS color, INSERTED.apid AS id)
            VALUES (%(color)s)
        """).with_data(color=apple.color)

    def select(self, apple_id: str) -> DatabaseCommand:
        return DatabaseCommand("""
            SELECT [clr] AS color, [apid] AS id
            FROM test.apples
            WHERE [apid] = %(id)s
        """).with_data(id=apple_id)

    def select_all(self) -> DatabaseCommand:
        return DatabaseCommand("""
            SELECT [clr] AS color, [apid] AS id
            FROM test.apples
        """)

    def delete(self, apple_id: str) -> DatabaseCommand:
        return DatabaseCommand("""
            DELETE FROM test.apples
            WHERE [apid] = %(id)s
        """).with_data(id=apple_id)

    def delete_all(self) -> DatabaseCommand:
        return DatabaseCommand("""
            DELETE FROM test.apples
        """)

    def update(self, apple: AppleMsSqlItem) -> DatabaseCommand:
        return DatabaseCommand("""
            UPDATE test.apples
            SET [clr] = %(color)s
            WHERE [apid] = %(id)s
        """).with_data(self.dump(apple))

    def load(self, data: Mapping[str, Any]) -> AppleMsSqlItem:
        return AppleMsSqlItem(color=str(data["color"]), id=str(data["id"]))

    def dump(self, apple: AppleMsSqlItem) -> dict[str, Any]:
        return {
            "color": apple.color,
            "id": apple.id,
        }

    def exists(self, duplicate: AppleMsSqlItem) -> ExistsError:
        return ExistsError(duplicate).with_duplicate(lambda _: f"id<{duplicate.id}>")


@pytest.fixture
def apple() -> AppleMsSqlItem:
    return AppleMsSqlItem(color="red")


def test_should_retrieve_all(apple: AppleMsSqlItem) -> None:
    db = MagicMock(spec=Database)
    executor = MagicMock(spec=Database._CommandExecutor)
    db.execute.return_value = executor
    table = AppleTable()

    executor.fetch_all.return_value = [table.dump(apple)]
    result = list(iter(MsSqlRepository[AppleMsSqlItem](db, table)))

    db.execute.assert_called_once_with(table.select_all())
    executor.fetch_all.assert_called_once()
    assert result == [apple]


def test_should_count_all() -> None:
    db = MagicMock(spec=Database)
    executor = MagicMock(spec=Database._CommandExecutor)
    db.execute.return_value = executor
    table = AppleTable()

    executor.fetch_one.return_value = {"n_items": 1}
    result = len(MsSqlRepository[AppleMsSqlItem](db, table))

    db.execute.assert_called_once_with(table.count_all())
    executor.fetch_one.assert_called_once()
    assert result == 1


def test_should_not_count_all() -> None:
    db = MagicMock(spec=Database)
    executor = MagicMock(spec=Database._CommandExecutor)
    db.execute.return_value = executor
    table = AppleTable()

    executor.fetch_one.return_value = {}
    with pytest.raises(UnknownError):
        len(MsSqlRepository[AppleMsSqlItem](db, table))


def test_should_delete(apple: AppleMsSqlItem) -> None:
    db = MagicMock(spec=Database)
    executor = MagicMock(spec=Database._CommandExecutor)
    db.execute.return_value = executor
    table = AppleTable()

    MsSqlRepository[AppleMsSqlItem](db, table).delete(apple.id)

    db.execute.assert_called_once_with(table.delete(apple.id))
    executor.fetch_none.assert_called_once()


def test_should_delete_all() -> None:
    db = MagicMock(spec=Database)
    executor = MagicMock(spec=Database._CommandExecutor)
    db.execute.return_value = executor
    table = AppleTable()

    MsSqlRepository[AppleMsSqlItem](db, table).delete_all()

    db.execute.assert_called_once_with(table.delete_all())
    executor.fetch_none.assert_called_once()


def test_should_create(apple: AppleMsSqlItem) -> None:
    db = MagicMock(spec=Database)
    executor = MagicMock(spec=Database._CommandExecutor)
    db.execute.return_value = executor
    table = AppleTable()

    executor.fetch_one.return_value = AppleTable().dump(apple)

    result = MsSqlRepository[AppleMsSqlItem](db, table).create(apple)

    db.execute.assert_called_once_with(table.insert(apple))
    executor.fetch_one.assert_called_once()
    assert result == apple


def test_should_not_duplicate(apple: AppleMsSqlItem) -> None:
    db = MagicMock(spec=Database)
    executor = MagicMock(spec=Database._CommandExecutor)
    db.execute.return_value = executor
    table = AppleTable()

    db.execute.side_effect = DatabaseError(2627, b"duplication")

    with pytest.raises(ExistsError):
        MsSqlRepository[AppleMsSqlItem](db, table).create(apple)


def test_should_not_create(apple: AppleMsSqlItem) -> None:
    db = MagicMock(spec=Database)
    executor = MagicMock(spec=Database._CommandExecutor)
    db.execute.return_value = executor
    table = AppleTable()

    db.execute.side_effect = DatabaseError(0, b"error")

    with pytest.raises(UnknownError):
        MsSqlRepository[AppleMsSqlItem](db, table).create(apple)


def test_should_read(apple: AppleMsSqlItem) -> None:
    db = MagicMock(spec=Database)
    executor = MagicMock(spec=Database._CommandExecutor)
    db.execute.return_value = executor
    table = AppleTable()

    executor.fetch_one.return_value = AppleTable().dump(apple)

    result = MsSqlRepository[AppleMsSqlItem](db, table).read(apple.id)

    db.execute.assert_called_once_with(table.select(apple.id))
    executor.fetch_one.assert_called_once()
    assert result == apple


def test_should_not_read_unknown(apple: AppleMsSqlItem) -> None:
    db = MagicMock(spec=Database)
    executor = MagicMock(spec=Database._CommandExecutor)
    db.execute.return_value = executor
    table = AppleTable()

    executor.fetch_one.return_value = None

    with pytest.raises(DoesNotExistError):
        MsSqlRepository[AppleMsSqlItem](db, table).read(apple.id)


def test_should_update(apple: AppleMsSqlItem) -> None:
    db = MagicMock(spec=Database)
    executor = MagicMock(spec=Database._CommandExecutor)
    db.execute.return_value = executor
    table = AppleTable()

    MsSqlRepository[AppleMsSqlItem](db, table).update(apple)

    db.execute.assert_called_once_with(table.update(apple))
    executor.fetch_none.assert_called_once()

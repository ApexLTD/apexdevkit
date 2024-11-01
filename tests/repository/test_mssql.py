from dataclasses import dataclass, field
from typing import Any
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from pymssql.exceptions import DatabaseError
from pytest import fixture

from apexdevkit.error import DoesNotExistError, ExistsError
from apexdevkit.repository import Database, DatabaseCommand, MsSqlRepository
from apexdevkit.repository.mssql import SqlTable, UnknownError


@dataclass
class Apple:
    color: str

    id: str = field(default_factory=lambda: str(uuid4()))


class AppleTable(SqlTable[Apple]):
    def count_all(self) -> DatabaseCommand:
        return DatabaseCommand("SELECT COUNT(*) AS n_items FROM test.apples")

    def insert(self, apple: Apple) -> DatabaseCommand:
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

    def update(self, apple: Apple) -> DatabaseCommand:
        return DatabaseCommand("""
            UPDATE test.apples
            SET [clr] = %(color)s 
            WHERE [apid] = %(id)s
        """).with_data(self.dump(apple))

    def load(self, data: dict[str, Any]) -> Apple:
        return Apple(color=str(data["color"]), id=str(data["id"]))

    def dump(self, apple: Apple) -> dict[str, Any]:
        return {
            "color": apple.color,
            "id": apple.id,
        }

    def exists(self, duplicate: Apple) -> ExistsError:
        return ExistsError(duplicate).with_duplicate(lambda i: f"id<{duplicate.id}>")


@fixture
def apple() -> Apple:
    return Apple("red")


def test_should_retrieve_all(apple: Apple) -> None:
    db = MagicMock(spec=Database)
    executor = MagicMock(spec=Database._CommandExecutor)
    db.execute.return_value = executor
    table = AppleTable()

    executor.fetch_all.return_value = [table.dump(apple)]
    result = [item for item in MsSqlRepository[Apple](db, table)]

    db.execute.assert_called_once_with(table.select_all())
    executor.fetch_all.assert_called_once()
    assert result == [apple]


def test_should_count_all() -> None:
    db = MagicMock(spec=Database)
    executor = MagicMock(spec=Database._CommandExecutor)
    db.execute.return_value = executor
    table = AppleTable()

    executor.fetch_one.return_value = {"n_items": 1}
    result = len(MsSqlRepository[Apple](db, table))

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
        len(MsSqlRepository[Apple](db, table))


def test_should_delete(apple: Apple) -> None:
    db = MagicMock(spec=Database)
    executor = MagicMock(spec=Database._CommandExecutor)
    db.execute.return_value = executor
    table = AppleTable()

    MsSqlRepository[Apple](db, table).delete(apple.id)

    db.execute.assert_called_once_with(table.delete(apple.id))
    executor.fetch_none.assert_called_once()


def test_should_delete_all() -> None:
    db = MagicMock(spec=Database)
    executor = MagicMock(spec=Database._CommandExecutor)
    db.execute.return_value = executor
    table = AppleTable()

    MsSqlRepository[Apple](db, table).delete_all()

    db.execute.assert_called_once_with(table.delete_all())
    executor.fetch_none.assert_called_once()


def test_should_create(apple: Apple) -> None:
    db = MagicMock(spec=Database)
    executor = MagicMock(spec=Database._CommandExecutor)
    db.execute.return_value = executor
    table = AppleTable()

    executor.fetch_one.return_value = AppleTable().dump(apple)

    result = MsSqlRepository[Apple](db, table).create(apple)

    db.execute.assert_called_once_with(table.insert(apple))
    executor.fetch_one.assert_called_once()
    assert result == apple


def test_should_not_duplicate(apple: Apple) -> None:
    db = MagicMock(spec=Database)
    executor = MagicMock(spec=Database._CommandExecutor)
    db.execute.return_value = executor
    table = AppleTable()

    db.execute.side_effect = DatabaseError(2627, b"duplication")

    with pytest.raises(ExistsError):
        MsSqlRepository[Apple](db, table).create(apple)


def test_should_not_create(apple: Apple) -> None:
    db = MagicMock(spec=Database)
    executor = MagicMock(spec=Database._CommandExecutor)
    db.execute.return_value = executor
    table = AppleTable()

    db.execute.side_effect = DatabaseError(0, b"error")

    with pytest.raises(UnknownError):
        MsSqlRepository[Apple](db, table).create(apple)


def test_should_read(apple: Apple) -> None:
    db = MagicMock(spec=Database)
    executor = MagicMock(spec=Database._CommandExecutor)
    db.execute.return_value = executor
    table = AppleTable()

    executor.fetch_one.return_value = AppleTable().dump(apple)

    result = MsSqlRepository[Apple](db, table).read(apple.id)

    db.execute.assert_called_once_with(table.select(apple.id))
    executor.fetch_one.assert_called_once()
    assert result == apple


def test_should_not_read_unknown(apple: Apple) -> None:
    db = MagicMock(spec=Database)
    executor = MagicMock(spec=Database._CommandExecutor)
    db.execute.return_value = executor
    table = AppleTable()

    executor.fetch_one.return_value = None

    with pytest.raises(DoesNotExistError):
        MsSqlRepository[Apple](db, table).read(apple.id)


def test_should_update(apple: Apple) -> None:
    db = MagicMock(spec=Database)
    executor = MagicMock(spec=Database._CommandExecutor)
    db.execute.return_value = executor
    table = AppleTable()

    MsSqlRepository[Apple](db, table).update(apple)

    db.execute.assert_called_once_with(table.update(apple))
    executor.fetch_none.assert_called_once()

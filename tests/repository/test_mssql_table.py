from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from pytest import fixture

from apexdevkit.repository import DatabaseCommand
from apexdevkit.repository.mssql import MsSqlTableBuilder, SqlTable


@dataclass
class Apple:
    color: str
    parent: str | None

    id: str = field(default_factory=lambda: str(uuid4()))


@dataclass
class AppleFormatter:
    def dump(self, data: Apple) -> dict[str, Any]:
        return {"apid": data.id, "clr": data.color, "pid": data.parent}

    def load(self, raw: dict[str, Any]) -> Apple:
        return Apple(raw["clr"], raw["pid"], raw["apid"])


@fixture
def table() -> SqlTable[Apple]:
    return (
        MsSqlTableBuilder()
        .with_username("test")
        .with_schema("test")
        .with_table("apples")
        .with_fields(["apid", "clr", "pid"])
        .with_id("apid")
        .with_order_fields(["apid"])
        .with_formatter(AppleFormatter())  # type: ignore
        .build()
    )


@fixture()
def table_with_parent() -> SqlTable[Apple]:
    return (
        MsSqlTableBuilder()
        .with_username("test")
        .with_schema("test")
        .with_table("apples")
        .with_fields(["apid", "clr", "pid"])
        .with_id("apid")
        .with_order_fields(["apid"])
        .with_parent("pid", "test")
        .with_formatter(AppleFormatter())  # type: ignore
        .build()
    )


@fixture
def apple() -> Apple:
    return Apple("red", "1", "1")


def test_should_count(table: SqlTable[Apple]) -> None:
    command = table.count_all()
    assert command == DatabaseCommand(
        """
            EXECUTE AS USER = 'test'
            SELECT count(*) AS n_items
            FROM [test].[apples]
            
            REVERT
        """
    )


def test_should_insert(table: SqlTable[Apple], apple: Apple) -> None:
    command = table.insert(apple)
    assert command == DatabaseCommand(
        """
            EXECUTE AS USER = 'test'
            INSERT INTO [test].[apples] (
                [apid], [clr], [pid]
            ) OUTPUT
                INSERTED.apid, INSERTED.clr, INSERTED.pid
            VALUES (
                %(apid)s, %(clr)s, %(pid)s
            )
            REVERT
        """
    ).with_data(AppleFormatter().dump(apple))


def test_should_select(table: SqlTable[Apple], apple: Apple) -> None:
    command = table.select(apple.id)
    assert command == DatabaseCommand(
        """
            EXECUTE AS USER = 'test'
            SELECT
                [apid], [clr], [pid] 
            FROM [test].[apples]
            WHERE [apid] = %(apid)s
            REVERT
        """
    ).with_data(apid=apple.id)


def test_should_select_all(table: SqlTable[Apple]) -> None:
    command = table.select_all()
    assert (
        command
        == DatabaseCommand(
            """
            EXECUTE AS USER = 'test'
            SELECT
                [apid], [clr], [pid]
            FROM [test].[apples]
            
            ORDER BY apid
            REVERT
        """
        ).with_data()
    )


def test_should_update(table: SqlTable[Apple], apple: Apple) -> None:
    command = table.update(apple)
    assert command == DatabaseCommand(
        """
            EXECUTE AS USER = 'test'
            UPDATE [test].[apples]
            SET
                clr = %(clr)s, pid = %(pid)s
            WHERE [apid] = %(apid)s
            REVERT
        """
    ).with_data(AppleFormatter().dump(apple))


def test_should_delete(table: SqlTable[Apple], apple: Apple) -> None:
    command = table.delete(apple.id)
    assert command == DatabaseCommand(
        """
            EXECUTE AS USER = 'test'
            DELETE
            FROM [test].[apples]
            WHERE [apid] = %(apid)s
            REVERT
        """
    ).with_data(apid=apple.id)


def test_should_delete_all(table: SqlTable[Apple]) -> None:
    command = table.delete_all()
    assert (
        command
        == DatabaseCommand(
            """
            EXECUTE AS USER = 'test'
            DELETE
            FROM [test].[apples]
            
            REVERT
        """
        ).with_data()
    )


def test_should_count_with_parent(table_with_parent: SqlTable[Apple]) -> None:
    command = table_with_parent.count_all()
    assert command == DatabaseCommand(
        """
            EXECUTE AS USER = 'test'
            SELECT count(*) AS n_items
            FROM [test].[apples]
            WHERE [pid] = 'test'
            REVERT
        """
    )


def test_should_insert_with_parent(
    table_with_parent: SqlTable[Apple], apple: Apple
) -> None:
    command = table_with_parent.insert(apple)
    dumped = AppleFormatter().dump(apple)
    dumped["pid"] = "test"

    assert command == DatabaseCommand(
        """
            EXECUTE AS USER = 'test'
            INSERT INTO [test].[apples] (
                [apid], [clr], [pid]
            ) OUTPUT
                INSERTED.apid, INSERTED.clr, INSERTED.pid
            VALUES (
                %(apid)s, %(clr)s, %(pid)s
            )
            REVERT
        """
    ).with_data(dumped)


def test_should_select_with_parent(
    table_with_parent: SqlTable[Apple], apple: Apple
) -> None:
    command = table_with_parent.select(apple.id)
    assert command == DatabaseCommand(
        """
            EXECUTE AS USER = 'test'
            SELECT
                [apid], [clr], [pid] 
            FROM [test].[apples]
            WHERE [apid] = %(apid)s AND [pid] = %(pid)s
            REVERT
        """
    ).with_data(apid=apple.id, pid="test")


def test_should_select_all_with_parent(table_with_parent: SqlTable[Apple]) -> None:
    command = table_with_parent.select_all()
    assert (
        command
        == DatabaseCommand(
            """
            EXECUTE AS USER = 'test'
            SELECT
                [apid], [clr], [pid]
            FROM [test].[apples]
            WHERE [pid] = 'test'
            ORDER BY apid
            REVERT
        """
        ).with_data()
    )


def test_should_update_with_parent(
    table_with_parent: SqlTable[Apple], apple: Apple
) -> None:
    command = table_with_parent.update(apple)
    dumped = AppleFormatter().dump(apple)
    dumped["pid"] = "test"

    assert command == DatabaseCommand(
        """
            EXECUTE AS USER = 'test'
            UPDATE [test].[apples]
            SET
                clr = %(clr)s
            WHERE [apid] = %(apid)s AND [pid] = %(pid)s
            REVERT
        """
    ).with_data(dumped)


def test_should_delete_with_parent(
    table_with_parent: SqlTable[Apple], apple: Apple
) -> None:
    command = table_with_parent.delete(apple.id)

    assert command == DatabaseCommand(
        """
            EXECUTE AS USER = 'test'
            DELETE
            FROM [test].[apples]
            WHERE [apid] = %(apid)s AND [pid] = %(pid)s
            REVERT
        """
    ).with_data(apid=apple.id, pid="test")


def test_should_delete_all_with_parent(table_with_parent: SqlTable[Apple]) -> None:
    command = table_with_parent.delete_all()

    assert (
        command
        == DatabaseCommand(
            """
            EXECUTE AS USER = 'test'
            DELETE
            FROM [test].[apples]
            WHERE [pid] = 'test'
            REVERT
        """
        ).with_data()
    )

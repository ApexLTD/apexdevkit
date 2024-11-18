from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from pytest import fixture

from apexdevkit.repository import DatabaseCommand
from apexdevkit.repository.mssql import MsSqlTableBuilder, SqlTable


@dataclass
class Apple:
    color: str

    id: str = field(default_factory=lambda: str(uuid4()))


@dataclass
class AppleFormatter:
    def dump(self, data: Apple) -> dict[str, Any]:
        return {"apid": data.id, "clr": data.color}

    def load(self, raw: dict[str, Any]) -> Apple:
        return Apple(raw["clr"], raw["apid"])


@fixture
def table() -> SqlTable[Apple]:
    return (
        MsSqlTableBuilder()
        .with_username("test")
        .with_schema("test")
        .with_table("apples")
        .with_fields(["apid", "clr"])
        .with_id("apid")
        .with_order_fields(["apid"])
        .with_formatter(AppleFormatter())  # type: ignore
        .build()
    )


@fixture
def apple() -> Apple:
    return Apple("red", "1")


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
                [apid], [clr]
            ) OUTPUT
                INSERTED.apid, INSERTED.clr
            VALUES (
                %(apid)s, %(clr)s
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
                [apid], [clr] 
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
                [apid], [clr]
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
                clr = %(clr)s
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

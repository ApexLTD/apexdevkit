from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping
from uuid import uuid4

from pytest import fixture

from apexdevkit.repository import DatabaseCommand
from apexdevkit.repository.mssql import MsSqlTableBuilder, SqlTable
from apexdevkit.repository.sql import SqlFieldBuilder


@dataclass
class Fruit:
    color: str
    parent: str | None
    type: FruitType

    id: str = field(default_factory=lambda: str(uuid4()))


class FruitType(str, Enum):
    apple = "apple"
    pear = "pear"


class _Formatter:
    def load(self, raw: Mapping[str, Any]) -> Fruit:
        return Fruit(
            id="apple_" + str(raw["apid"])
            if raw["type"] == "apple"
            else "pear_" + str(raw["apid"]),
            color=raw["clr"],
            type=FruitType[raw["type"]],
            parent=raw["pid"],
        )

    def dump(self, fruit: Fruit) -> Mapping[str, Any]:
        return {
            "apid": self._dump_id(fruit.id),
            "clr": fruit.color,
            "type": fruit.type.value,
            "pid": fruit.parent,
        }

    def _dump_id(self, identifier: str) -> int | None:
        if identifier.startswith("apple_"):
            return int(identifier.replace("apple_", ""))
        elif identifier.startswith("pear_"):
            return int(identifier.replace("pear_", ""))
        else:
            return None


@fixture
def table() -> SqlTable[Fruit]:
    return (
        MsSqlTableBuilder[Fruit]()
        .with_username("test")
        .with_schema("test")
        .with_table("apples")
        .and_table("pears")
        .with_table_mapper(
            lambda fruit: "apples" if fruit.type == FruitType.apple else "pears"
        )
        .with_table_id_mapper(
            lambda identifier: "apples" if identifier.startswith("apple_") else "pears"
        )
        .with_id_transformer(
            lambda identifier: identifier.replace("apple_", "").replace("pear_", ""),
        )
        .with_formatter(_Formatter())
        .with_fields(
            [
                SqlFieldBuilder().with_name("apid").as_id().in_ordering().build(),
                SqlFieldBuilder().with_name("clr").build(),
                SqlFieldBuilder().with_name("pid").build(),
                SqlFieldBuilder().with_name("type").build(),
                SqlFieldBuilder().with_name("kingdom").as_fixed("fruits").build(),
                (
                    SqlFieldBuilder()
                    .with_name("manager")
                    .as_fixed(None)
                    .as_filter([5, 4])
                    .build()
                ),
            ]
        )
        .build()
    )


@fixture
def apple() -> Fruit:
    return Fruit(color="red", parent="test", type=FruitType.apple, id="apple_1")


@fixture
def pear() -> Fruit:
    return Fruit(color="blue", parent="test", type=FruitType.pear, id="pear_1")


def test_should_count(table: SqlTable[Fruit]) -> None:
    command = table.count_all()
    assert command == DatabaseCommand(
        """
            EXECUTE AS USER = 'test'
            SELECT
            (
                SELECT COUNT(*)
                FROM [test].[apples]
                WHERE ([manager] = %(manager_filter_0)s OR [manager]"""
        + """ = %(manager_filter_1)s)
            ) + (
                SELECT COUNT(*)
                FROM [test].[pears]
                WHERE ([manager] = %(manager_filter_0)s OR [manager]"""
        + """ = %(manager_filter_1)s)
            ) AS n_items
            REVERT
        """
    ).with_data(kingdom="fruits", manager=None, manager_filter_0=5, manager_filter_1=4)


def test_should_insert(table: SqlTable[Fruit], pear: Fruit) -> None:
    command = table.insert(pear)
    assert command == DatabaseCommand(
        """
            EXECUTE AS USER = 'test'
            INSERT INTO [test].[pears] (
                [apid], [clr], [pid], [type], [kingdom], [manager]
            )
            VALUES (
                %(apid)s, %(clr)s, %(pid)s, %(type)s, %(kingdom)s, %(manager)s
            );
            SELECT
                [apid] AS apid, [clr] AS clr, [pid] AS pid, [type] AS type, """
        + """[kingdom] AS kingdom, [manager] AS manager
            
                FROM [test].[pears]
                WHERE [apid] = %(apid)s AND ([manager] = %(manager_filter_0)s """
        + """OR [manager] = %(manager_filter_1)s)
            
            REVERT
        """
    ).with_data(
        kingdom="fruits",
        manager=None,
        manager_filter_0=5,
        manager_filter_1=4,
        **_Formatter().dump(pear),
    )


def test_should_select(table: SqlTable[Fruit], apple: Fruit) -> None:
    command = table.select(apple.id)
    assert command == DatabaseCommand(
        """
            EXECUTE AS USER = 'test'
            SELECT
                [apid], [clr], [pid], [type], [kingdom], [manager] 
            FROM [test].[apples]
            WHERE [apid] = %(apid)s AND ([manager] = %(manager_filter_0)s OR """
        + """[manager] = %(manager_filter_1)s)
            REVERT
        """
    ).with_data(
        apid=apple.id.replace("apple_", ""),
        manager=None,
        manager_filter_0=5,
        manager_filter_1=4,
        kingdom="fruits",
    )


def test_should_select_all(table: SqlTable[Fruit]) -> None:
    command = table.select_all()
    assert command == DatabaseCommand(
        """
            EXECUTE AS USER = 'test'
            SELECT
                [apid], [clr], [pid], [type], [kingdom], [manager]
            FROM [test].[apples]
            WHERE ([manager] = %(manager_filter_0)s OR [manager] = """
        + """%(manager_filter_1)s)
            UNION ALL
            SELECT
                [apid], [clr], [pid], [type], [kingdom], [manager]
            FROM [test].[pears]
            WHERE ([manager] = %(manager_filter_0)s OR [manager] = """
        + """%(manager_filter_1)s)
            ORDER BY apid
            REVERT
        """
    ).with_data(kingdom="fruits", manager=None, manager_filter_0=5, manager_filter_1=4)


def test_should_update(table: SqlTable[Fruit], pear: Fruit) -> None:
    command = table.update(pear)
    assert command == DatabaseCommand(
        """
            EXECUTE AS USER = 'test'
            UPDATE [test].[pears]
            SET
                clr = %(clr)s, pid = %(pid)s, """
        + """type = %(type)s, kingdom = %(kingdom)s, manager = %(manager)s
            WHERE [apid] = %(apid)s AND ([manager] = %(manager_filter_0)s """
        + """OR [manager] = %(manager_filter_1)s)
            REVERT
        """
    ).with_data(
        kingdom="fruits",
        manager=None,
        manager_filter_0=5,
        manager_filter_1=4,
        **_Formatter().dump(pear),
    )


def test_should_delete(table: SqlTable[Fruit], pear: Fruit) -> None:
    command = table.delete(pear.id)
    assert command == DatabaseCommand(
        """
            EXECUTE AS USER = 'test'
            DELETE
            FROM [test].[pears]
            WHERE [apid] = %(apid)s AND ([manager] = %(manager_filter_0)s"""
        + """ OR [manager] = %(manager_filter_1)s)
            REVERT
        """
    ).with_data(
        apid=pear.id.replace("pear_", ""),
        kingdom="fruits",
        manager=None,
        manager_filter_0=5,
        manager_filter_1=4,
    )

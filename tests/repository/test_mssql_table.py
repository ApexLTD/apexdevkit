from dataclasses import dataclass, field
from uuid import uuid4

from pytest import fixture

from apexdevkit.formatter import AliasFormatter, AliasMapping, DataclassFormatter
from apexdevkit.repository import DatabaseCommand
from apexdevkit.repository.mssql import MsSqlTableBuilder, SqlTable
from apexdevkit.repository.sql import SqlFieldBuilder


@dataclass
class Apple:
    color: str
    parent: str | None

    id: str = field(default_factory=lambda: str(uuid4()))


_FORMATTER = AliasFormatter(
    DataclassFormatter(Apple),
    alias=AliasMapping.parse(
        id="apid",
        color="clr",
        parent="pid",
    ),
)


@fixture
def table() -> SqlTable[Apple]:
    return (
        MsSqlTableBuilder[Apple]()
        .with_username("test")
        .with_schema("test")
        .with_table("apples")
        .with_formatter(_FORMATTER)
        .with_fields(
            [
                SqlFieldBuilder().with_name("apid").as_id().in_ordering().build(),
                SqlFieldBuilder().with_name("clr").build(),
                SqlFieldBuilder().with_name("pid").build(),
                SqlFieldBuilder().with_name("kingdom").as_fixed("fruits").build(),
                SqlFieldBuilder()
                .with_name("manager")
                .as_fixed(None)
                .as_filter([5, 4])
                .build(),
            ]
        )
        .build()
    )


@fixture
def apple() -> Apple:
    return Apple(color="red", parent="test", id="1")


@fixture
def table_with_parent(apple: Apple) -> SqlTable[Apple]:
    return (
        MsSqlTableBuilder[Apple]()
        .with_username("test")
        .with_schema("test")
        .with_table("apples")
        .with_formatter(_FORMATTER)
        .with_fields(
            [
                SqlFieldBuilder().with_name("apid").as_id().in_ordering().build(),
                SqlFieldBuilder().with_name("clr").build(),
                SqlFieldBuilder().with_name("pid").as_parent(apple.parent).build(),
            ]
        )
        .build()
    )


def test_should_count(table: SqlTable[Apple]) -> None:
    command = table.count_all()
    assert command == DatabaseCommand(
        """
            EXECUTE AS USER = 'test'
            SELECT count(*) AS n_items
            FROM [test].[apples]
            WHERE ([manager] = %(manager_filter_0)s OR [manager] = """
        + """%(manager_filter_1)s)
            REVERT
        """
    ).with_data(kingdom="fruits", manager=None, manager_filter_0=5, manager_filter_1=4)


def test_should_insert(table: SqlTable[Apple], apple: Apple) -> None:
    command = table.insert(apple)
    assert command == DatabaseCommand(
        """
            EXECUTE AS USER = 'test'
            INSERT INTO [test].[apples] (
                [apid], [clr], [pid], [kingdom], [manager]
            )
            VALUES (
                %(apid)s, %(clr)s, %(pid)s, %(kingdom)s, %(manager)s
            );
            SELECT
                [apid] AS apid, [clr] AS clr, [pid] AS pid, [kingdom] AS kingdom,"""
        + """ [manager] AS manager
            
                FROM [test].[apples]
                WHERE [apid] = %(apid)s AND ([manager] = %(manager_filter_0)s """
        + """OR [manager] = %(manager_filter_1)s)
            
            REVERT
        """
    ).with_data(
        kingdom="fruits",
        manager=None,
        manager_filter_0=5,
        manager_filter_1=4,
        **_FORMATTER.dump(apple),
    )


def test_should_select(table: SqlTable[Apple], apple: Apple) -> None:
    command = table.select(apple.id)
    assert command == DatabaseCommand(
        """
            EXECUTE AS USER = 'test'
            SELECT
                [apid], [clr], [pid], [kingdom], [manager] 
            FROM [test].[apples]
            WHERE [apid] = %(apid)s AND ([manager] = %(manager_filter_0)s OR """
        + """[manager] = %(manager_filter_1)s)
            REVERT
        """
    ).with_data(
        apid=apple.id,
        manager=None,
        manager_filter_0=5,
        manager_filter_1=4,
        kingdom="fruits",
    )


def test_should_select_all(table: SqlTable[Apple]) -> None:
    command = table.select_all()
    assert command == DatabaseCommand(
        """
            EXECUTE AS USER = 'test'
            SELECT
                [apid], [clr], [pid], [kingdom], [manager]
            FROM [test].[apples]
            WHERE ([manager] = %(manager_filter_0)s OR [manager] = """
        + """%(manager_filter_1)s)
            ORDER BY apid
            REVERT
        """
    ).with_data(kingdom="fruits", manager=None, manager_filter_0=5, manager_filter_1=4)


def test_should_update(table: SqlTable[Apple], apple: Apple) -> None:
    command = table.update(apple)
    assert command == DatabaseCommand(
        """
            EXECUTE AS USER = 'test'
            UPDATE [test].[apples]
            SET
                clr = %(clr)s, pid = %(pid)s, """
        + """kingdom = %(kingdom)s, manager = %(manager)s
            WHERE [apid] = %(apid)s AND ([manager] = %(manager_filter_0)s """
        + """OR [manager] = %(manager_filter_1)s)
            REVERT
        """
    ).with_data(
        kingdom="fruits",
        manager=None,
        manager_filter_0=5,
        manager_filter_1=4,
        **_FORMATTER.dump(apple),
    )


def test_should_delete(table: SqlTable[Apple], apple: Apple) -> None:
    command = table.delete(apple.id)
    assert command == DatabaseCommand(
        """
            EXECUTE AS USER = 'test'
            DELETE
            FROM [test].[apples]
            WHERE [apid] = %(apid)s AND ([manager] = %(manager_filter_0)s"""
        + """ OR [manager] = %(manager_filter_1)s)
            REVERT
        """
    ).with_data(
        apid=apple.id,
        kingdom="fruits",
        manager=None,
        manager_filter_0=5,
        manager_filter_1=4,
    )


def test_should_delete_all(table: SqlTable[Apple]) -> None:
    command = table.delete_all()
    assert command == DatabaseCommand(
        """
            EXECUTE AS USER = 'test'
            DELETE
            FROM [test].[apples]
            WHERE ([manager] = %(manager_filter_0)s OR """
        + """[manager] = %(manager_filter_1)s)
            REVERT
        """
    ).with_data(kingdom="fruits", manager=None, manager_filter_0=5, manager_filter_1=4)


def test_should_count_with_parent(table_with_parent: SqlTable[Apple]) -> None:
    command = table_with_parent.count_all()
    assert command == DatabaseCommand(
        """
            EXECUTE AS USER = 'test'
            SELECT count(*) AS n_items
            FROM [test].[apples]
            WHERE [pid] = %(pid)s
            REVERT
        """
    ).with_data(pid="test")


def test_should_insert_with_parent(
    table_with_parent: SqlTable[Apple], apple: Apple
) -> None:
    command = table_with_parent.insert(apple)
    dumped = _FORMATTER.dump(apple)

    assert command == DatabaseCommand(
        """
            EXECUTE AS USER = 'test'
            INSERT INTO [test].[apples] (
                [apid], [clr], [pid]
            )
            VALUES (
                %(apid)s, %(clr)s, %(pid)s
            );
            SELECT
                [apid] AS apid, [clr] AS clr, [pid] AS pid
            
                FROM [test].[apples]
                WHERE [pid] = %(pid)s AND [apid] = %(apid)s
            
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
            WHERE [pid] = %(pid)s AND [apid] = %(apid)s
            REVERT
        """
    ).with_data(apid=apple.id, pid="test")


def test_should_select_all_with_parent(table_with_parent: SqlTable[Apple]) -> None:
    command = table_with_parent.select_all()
    assert command == DatabaseCommand(
        """
            EXECUTE AS USER = 'test'
            SELECT
                [apid], [clr], [pid]
            FROM [test].[apples]
            WHERE [pid] = %(pid)s
            ORDER BY apid
            REVERT
        """
    ).with_data(pid="test")


def test_should_update_with_parent(
    table_with_parent: SqlTable[Apple], apple: Apple
) -> None:
    command = table_with_parent.update(apple)
    dumped = _FORMATTER.dump(apple)

    assert command == DatabaseCommand(
        """
            EXECUTE AS USER = 'test'
            UPDATE [test].[apples]
            SET
                clr = %(clr)s
            WHERE [pid] = %(pid)s AND [apid] = %(apid)s
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
            WHERE [pid] = %(pid)s AND [apid] = %(apid)s
            REVERT
        """
    ).with_data(apid=apple.id, pid="test")


def test_should_delete_all_with_parent(table_with_parent: SqlTable[Apple]) -> None:
    command = table_with_parent.delete_all()

    assert command == DatabaseCommand(
        """
            EXECUTE AS USER = 'test'
            DELETE
            FROM [test].[apples]
            WHERE [pid] = %(pid)s
            REVERT
        """
    ).with_data(pid="test")

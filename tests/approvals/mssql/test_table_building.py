from dataclasses import dataclass

import pytest
from pytest_apex import ApprovalCase

from apexdevkit.formatter import AliasFormatter, AliasMapping, DataclassFormatter
from apexdevkit.repository import Entity
from apexdevkit.repository.sql import MsSqlTableBuilder, SqlField
from apexdevkit.repository.sql.mssql import AsUser, SqlTable


@dataclass(frozen=True, kw_only=True)
class Apple(Entity):
    color: str

    parent: str | None = None


@pytest.fixture
def apple() -> Apple:
    return Apple(color="red", parent="test", id="1")


_FORMATTER = AliasFormatter(
    DataclassFormatter(Apple),
    alias=AliasMapping.parse(
        id="apid",
        color="clr",
        parent="pid",
    ),
)


TABLE_WITHOUT_PARENT = (
    MsSqlTableBuilder[Apple]()
    .with_schema("test")
    .with_table("apples")
    .with_a(sql_field=SqlField("apid").as_id().order_by(descending=True))
    .and_a(sql_field=SqlField("clr"))
    .and_a(sql_field=SqlField("pid"))
    .and_a(sql_field=SqlField("kingdom").fixed(value="fruits"))
    .and_a(sql_field=SqlField("manager").fixed(value=None).filter(values=[5, 4]))
    .with_custom_filters(["pid > 5"])
    .build()
    .with_a(formatter=_FORMATTER)
)

TABLE_WITH_PARENT = (
    MsSqlTableBuilder[Apple]()
    .with_schema("test")
    .with_table("apples")
    .with_a(sql_field=SqlField("apid").as_id().order_by())
    .with_a(sql_field=SqlField("clr"))
    .with_a(sql_field=SqlField("pid").parent("test"))
    .build()
    .with_a(formatter=_FORMATTER)
)

TABLE_WITHOUT_USERNAME = (
    MsSqlTableBuilder[Apple]()
    .with_schema("test")
    .with_table("apples")
    .with_a(sql_field=SqlField("apid").as_id())
    .with_a(sql_field=SqlField("clr"))
    .build()
    .with_a(formatter=_FORMATTER)
)


@pytest.fixture(
    params=[
        "with_username",
        "no_username",
        "with_parent",
        "no_parent",
    ]
)
def table(request: pytest.FixtureRequest) -> SqlTable[Apple]:
    match request.param:
        case "no_username":
            return TABLE_WITHOUT_USERNAME
        case "with_username":
            return AsUser(user="test", inner=TABLE_WITHOUT_USERNAME)
        case "with_parent":
            return TABLE_WITH_PARENT
        case "no_parent":
            return TABLE_WITHOUT_PARENT
        case _ as kind:
            raise RuntimeError(f"Unknown table type: {kind}")


def test_should_count(approve: ApprovalCase, table: SqlTable[Apple]) -> None:
    approve.sql().compact(str(table.count_all()))


def test_should_insert(
    approve: ApprovalCase,
    table: SqlTable[Apple],
    apple: Apple,
) -> None:
    approve.sql().compact(str(table.insert(apple)))


def test_should_select(
    approve: ApprovalCase,
    table: SqlTable[Apple],
    apple: Apple,
) -> None:
    approve.sql().compact(str(table.select(apple.id)))


def test_should_select_all(
    approve: ApprovalCase,
    table: SqlTable[Apple],
) -> None:
    approve.sql().compact(str(table.select_all()))


def test_should_update(
    approve: ApprovalCase,
    table: SqlTable[Apple],
    apple: Apple,
) -> None:
    approve.sql().compact(str(table.update(apple)))


def test_should_delete(
    approve: ApprovalCase,
    table: SqlTable[Apple],
    apple: Apple,
) -> None:
    approve.sql().compact(str(table.delete(apple.id)))


def test_should_delete_all(
    approve: ApprovalCase,
    table: SqlTable[Apple],
) -> None:
    approve.sql().compact(str(table.delete_all()))

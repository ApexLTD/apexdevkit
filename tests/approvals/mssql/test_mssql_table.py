from dataclasses import dataclass

import pytest
from pytest_apex import ApprovalCase

from apexdevkit.formatter import AliasFormatter, AliasMapping, DataclassFormatter
from apexdevkit.repository import Entity
from apexdevkit.repository.sql.field import SqlFieldBuilder
from apexdevkit.repository.sql.mssql import MsSqlTableBuilder, SqlTable


@dataclass(frozen=True, kw_only=True)
class Apple(Entity):
    color: str
    parent: str | None


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
    .with_username("test")
    .with_schema("test")
    .with_table("apples")
    .with_formatter(_FORMATTER)
    .with_fields(
        [
            SqlFieldBuilder()
            .with_name("apid")
            .as_id()
            .in_ordering(descending=True)
            .build(),
            SqlFieldBuilder().with_name("clr").build(),
            SqlFieldBuilder().with_name("pid").build(),
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
    .with_custom_filters(["pid > 5"])
    .build()
)

TABLE_WITH_PARENT = (
    MsSqlTableBuilder[Apple]()
    .with_username("test")
    .with_schema("test")
    .with_table("apples")
    .with_formatter(_FORMATTER)
    .with_fields(
        [
            SqlFieldBuilder().with_name("apid").as_id().in_ordering().build(),
            SqlFieldBuilder().with_name("clr").build(),
            SqlFieldBuilder().with_name("pid").as_parent("test").build(),
        ]
    )
    .build()
)


@pytest.fixture(params=["without_parent", "with_parent"])
def table(request: pytest.FixtureRequest) -> SqlTable[Apple]:
    match request.param:
        case "with_parent":
            return TABLE_WITH_PARENT
        case "without_parent":
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

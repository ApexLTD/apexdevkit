from pytest import fixture

from apexdevkit.formatter import AliasFormatter, AliasMapping, DataclassFormatter
from apexdevkit.repository.mssql import MsSqlTableBuilder, SqlTable
from apexdevkit.repository.sql import SqlFieldBuilder
from tests.repository.approvals.conftest import Apple
from tests.repository.approvals.extension import verify_sql

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


def test_should_count(table: SqlTable[Apple]) -> None:
    verify_sql(str(table.count_all()))


def test_should_insert(table: SqlTable[Apple], apple: Apple) -> None:
    verify_sql(str(table.insert(apple)))


def test_should_select(table: SqlTable[Apple], apple: Apple) -> None:
    verify_sql(str(table.select(apple.id)))


def test_should_select_all(table: SqlTable[Apple]) -> None:
    verify_sql(str(table.select_all()))


def test_should_update(table: SqlTable[Apple], apple: Apple) -> None:
    verify_sql(str(table.update(apple)))


def test_should_delete(table: SqlTable[Apple], apple: Apple) -> None:
    verify_sql(str(table.delete(apple.id)))


def test_should_delete_all(table: SqlTable[Apple]) -> None:
    verify_sql(str(table.delete_all()))

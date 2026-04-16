import pytest

from apexdevkit.formatter import AliasFormatter, AliasMapping, DataclassFormatter
from apexdevkit.repository.mssql import MsSqlTableBuilder, SqlTable
from apexdevkit.repository.sql import SqlFieldBuilder
from tests.approvals.conftest import Approver
from tests.approvals.repository.conftest import Apple

_FORMATTER = AliasFormatter(
    DataclassFormatter(Apple),
    alias=AliasMapping.parse(
        id="apid",
        color="clr",
        parent="pid",
    ),
)


@pytest.fixture
def table(apple: Apple) -> SqlTable[Apple]:
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


def test_should_count(approver: Approver, table: SqlTable[Apple]) -> None:
    approver.verify_sql("count", str(table.count_all()))


def test_should_insert(
    approver: Approver,
    table: SqlTable[Apple],
    apple: Apple,
) -> None:
    approver.verify_sql("insert", str(table.insert(apple)))


def test_should_select(
    approver: Approver,
    table: SqlTable[Apple],
    apple: Apple,
) -> None:
    approver.verify_sql("select", str(table.select(apple.id)))


def test_should_select_all(
    approver: Approver,
    table: SqlTable[Apple],
) -> None:
    approver.verify_sql("select_all", str(table.select_all()))


def test_should_update(
    approver: Approver,
    table: SqlTable[Apple],
    apple: Apple,
) -> None:
    approver.verify_sql("update", str(table.update(apple)))


def test_should_delete(
    approver: Approver,
    table: SqlTable[Apple],
    apple: Apple,
) -> None:
    approver.verify_sql("delete", str(table.delete(apple.id)))


def test_should_delete_all(
    approver: Approver,
    table: SqlTable[Apple],
) -> None:
    approver.verify_sql("delete_all", str(table.delete_all()))

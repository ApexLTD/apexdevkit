from typing import Any

import pytest

from apexdevkit.repository.sql.field import NotNone, SqlField
from apexdevkit.repository.sql.mssql.table import MsSqlTableBuilder


def test_with_fields_accepts_single_identifier_field() -> None:
    actual = (
        MsSqlTableBuilder[Any]()
        .with_a(sql_field=SqlField("id").as_id())
        .with_a(sql_field=SqlField("name"))
    )

    assert list(actual.fields) == [SqlField("id").as_id(), SqlField("name")]


def test_with_fields_raises_when_identifier_field_is_missing() -> None:
    with pytest.raises(ValueError, match=r"Id field is not provided."):
        MsSqlTableBuilder[Any]().build()


def test_with_fields_raises_when_multiple_identifier_fields_are_passed() -> None:
    with pytest.raises(ValueError, match=r"Pass only one identifier key."):
        (
            MsSqlTableBuilder[Any]()
            .with_a(sql_field=SqlField("id").as_id())
            .and_a(sql_field=SqlField("other_id").as_id())
        )


def test_with_fields_raises_when_multiple_parent_fields_are_passed() -> None:
    with pytest.raises(ValueError, match=r"Pass only one parent key."):
        (
            MsSqlTableBuilder[Any]()
            .with_a(sql_field=SqlField("id").as_id())
            .and_a(sql_field=SqlField("parent_id").parent(value=None))
            .and_a(sql_field=SqlField("other_parent_id").parent(value=None))
        )


def test_with_fields_raises_when_not_none_fixed_value_is_not_filter() -> None:
    with pytest.raises(ValueError, match=r"Only filter fields can be 'not null'."):
        (
            MsSqlTableBuilder[Any]()
            .with_a(sql_field=SqlField("id").as_id())
            .and_a(sql_field=SqlField("name").fixed(value=NotNone()))
        )


def test_build_raises_when_required_values_are_missing() -> None:
    with pytest.raises(ValueError, match=r"Cannot build sql table."):
        MsSqlTableBuilder[Any]().with_a(sql_field=SqlField("id").as_id()).build()

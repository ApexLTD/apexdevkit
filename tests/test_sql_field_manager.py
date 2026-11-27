import pytest

from apexdevkit.repository.sql.field import (
    NotNone,
    SqlField,
    SqlFieldManager,
    SqlFieldSet,
)


def test_id_returns_id_field_name() -> None:
    manager = (
        SqlFieldManager.Builder.for_sqlite()
        .with_fields(SqlFieldSet().add(SqlField("name")).add(SqlField("id").as_id()))
        .build()
    )

    assert manager.id_name == "id"


def test_id_raises_value_error_when_id_field_is_missing() -> None:
    manager = (
        SqlFieldManager.Builder.for_sqlite()
        .with_fields(SqlFieldSet().add(SqlField("name")))
        .build()
    )

    with pytest.raises(RuntimeError, match=r"FieldSet does not contain Id field."):
        _ = manager.id_name


def test_composite_returns_id_when_composite_fields_are_missing() -> None:
    manager = (
        SqlFieldManager.Builder.for_sqlite()
        .with_fields(SqlFieldSet().add(SqlField("id").as_id()).add(SqlField("name")))
        .build()
    )

    assert manager.composite == ["id"]


def test_composite_returns_composite_field_names() -> None:
    manager = (
        SqlFieldManager.Builder.for_sqlite()
        .with_fields(
            SqlFieldSet()
            .add(SqlField("id").as_id())
            .add(SqlField("tenant_id").composite())
            .add(SqlField("code").composite())
        )
        .build()
    )

    assert manager.composite == ["tenant_id", "code"]


def test_order_returns_empty_string_without_ordered_fields() -> None:
    manager = (
        SqlFieldManager.Builder.for_sqlite()
        .with_fields(SqlFieldSet().add(SqlField("id").as_id()))
        .build()
    )

    assert manager.order == ""


def test_order_returns_order_by_clause_for_ordered_fields() -> None:
    manager = (
        SqlFieldManager.Builder.for_sqlite()
        .with_fields(
            SqlFieldSet()
            .add(SqlField("id").as_id())
            .add(SqlField("name").order_by())
            .add(SqlField("created_at").order_by(descending=True))
        )
        .build()
    )

    assert manager.order == "ORDER BY name, created_at DESC"


def test_iter_yields_fields() -> None:
    manager = (
        SqlFieldManager.Builder.for_sqlite()
        .with_fields(SqlFieldSet().add(SqlField("id").as_id()).add(SqlField("name")))
        .build()
    )

    assert list(manager) == [SqlField("id").as_id(), SqlField("name")]


def test_where_statement_returns_empty_string_without_filters() -> None:
    manager = (
        SqlFieldManager.Builder.for_sqlite()
        .with_fields(SqlFieldSet().add(SqlField("id").as_id()))
        .build()
    )

    assert manager.where_statement() == ""


def test_where_statement_includes_parent_filter_with_value() -> None:
    manager = (
        SqlFieldManager.Builder.for_sqlite()
        .with_fields(
            SqlFieldSet()
            .add(SqlField("id").as_id())
            .add(SqlField("parent_id").parent(value=10))
        )
        .build()
    )

    assert manager.where_statement() == "WHERE parent_id = :parent_id"


def test_where_statement_includes_parent_filter_with_null_value() -> None:
    manager = (
        SqlFieldManager.Builder.for_sqlite()
        .with_fields(
            SqlFieldSet()
            .add(SqlField("id").as_id())
            .add(SqlField("parent_id").parent(value=None))
        )
        .build()
    )

    assert manager.where_statement() == "WHERE parent_id IS NULL"


def test_where_statement_includes_id_filter_when_requested() -> None:
    manager = (
        SqlFieldManager.Builder.for_sqlite()
        .with_fields(SqlFieldSet().add(SqlField("id").as_id()))
        .build()
    )

    assert manager.where_statement(include_id=True) == "WHERE id = :id"


def test_where_statement_includes_selectable_fields_in_id_filter() -> None:
    manager = (
        SqlFieldManager.Builder.for_sqlite()
        .with_fields(
            SqlFieldSet()
            .add(SqlField("id").as_id())
            .add(SqlField("external_id").selectable())
        )
        .build()
    )

    assert (
        manager.where_statement(include_id=True)
        == "WHERE (id = :id OR external_id = :id)"
    )


def test_where_statement_uses_scope_identity_for_read_id_when_not_inserted() -> None:
    manager = (
        SqlFieldManager.Builder.for_mssql()
        .with_fields(SqlFieldSet().add(SqlField("id").as_id().derive_on_insert()))
        .build()
    )

    assert (
        manager.where_statement(include_id=True, read_id=True)
        == "WHERE [id] = SCOPE_IDENTITY()"
    )


def test_where_statement_includes_custom_filters() -> None:
    manager = (
        SqlFieldManager.Builder.for_sqlite()
        .with_fields(SqlFieldSet().add(SqlField("id").as_id()))
        .with_custom_filters(["is_deleted = 0"])
        .build()
    )

    assert manager.where_statement() == "WHERE is_deleted = 0"


def test_where_statement_includes_general_filter_values() -> None:
    manager = (
        SqlFieldManager.Builder.for_sqlite()
        .with_fields(
            SqlFieldSet()
            .add(SqlField("id").as_id())
            .add(SqlField("status").filter(values=["active", "pending"]))
        )
        .build()
    )

    assert (
        manager.where_statement()
        == "WHERE (status = :status_filter_0 OR status = :status_filter_1)"
    )


def test_where_statement_includes_null_and_not_null_filters() -> None:
    manager = (
        SqlFieldManager.Builder.for_sqlite()
        .with_fields(
            SqlFieldSet()
            .add(SqlField("id").as_id())
            .add(SqlField("archived_at").filter(values=[None, NotNone()]))
        )
        .build()
    )

    assert (
        manager.where_statement()
        == "WHERE (archived_at IS NULL OR archived_at IS NOT NULL)"
    )


def test_with_fixed_adds_parent_fixed_and_filter_values() -> None:
    manager = (
        SqlFieldManager.Builder.for_sqlite()
        .with_fields(
            SqlFieldSet()
            .add(SqlField("id").as_id())
            .add(SqlField("parent_id").parent(value=10))
            .add(SqlField("kind").fixed(value="default"))
            .add(SqlField("status").filter(values=["active", None, NotNone()]))
        )
        .build()
    )

    assert manager.with_fixed({"name": "Example"}) == {
        "name": "Example",
        "parent_id": 10,
        "kind": "default",
        "status_filter_0": "active",
    }


def test_builder_creates_mssql_manager_with_mssql_formatters() -> None:
    manager = (
        SqlFieldManager.Builder.for_mssql()
        .with_fields(
            SqlFieldSet()
            .add(SqlField("id").as_id())
            .add(SqlField("parent_id").parent(value=10))
        )
        .build()
    )

    assert manager.where_statement() == "WHERE [parent_id] = %(parent_id)s"

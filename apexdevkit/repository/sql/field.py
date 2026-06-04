from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class NotNone:
    pass


@dataclass(frozen=True)
class _SqlField:
    name: str
    is_id: bool = False
    is_selectable: bool = False
    is_composite: bool = False
    include_in_insert: bool = True
    include_in_update: bool = True

    is_ordered: bool = False
    is_descending: bool = False

    is_parent: bool = False
    parent_value: Any | None = None

    is_filter: bool = False
    filter_values: list[Any | None | NotNone] = field(default_factory=list)

    is_fixed: bool = False
    fixed_value: Any | None = None


@dataclass
class SqlFieldBuilder:
    _name: str = field(init=False)
    _is_id: bool = False
    _is_selectable: bool = False
    _is_composite: bool = False
    _include_in_insert: bool = True
    _include_in_update: bool = True

    _is_ordered: bool = False
    _is_descending: bool = False

    _is_parent: bool = False
    _parent_value: Any | None = None

    _is_filter: bool = False
    _filter_values: list[Any | None | NotNone] = field(default_factory=list)

    _is_fixed: bool = False
    _fixed_value: Any | None = None

    def with_name(self, value: str) -> SqlFieldBuilder:
        self._name = value

        return self

    def as_id(self) -> SqlFieldBuilder:
        self._is_id = True

        return self

    def as_selectable(self) -> SqlFieldBuilder:
        self._is_selectable = True

        return self

    def as_composite(self) -> SqlFieldBuilder:
        self._is_composite = True

        return self

    def in_ordering(self, descending: bool = False) -> SqlFieldBuilder:
        self._is_ordered = True
        self._is_descending = descending

        return self

    def derive_on_insert(self) -> SqlFieldBuilder:
        self._include_in_insert = False

        return self

    def as_not_editable(self) -> SqlFieldBuilder:
        self._include_in_update = False

        return self

    def as_parent(self, value: Any | None) -> SqlFieldBuilder:
        self._is_parent = True
        self._parent_value = value

        return self

    def as_filter(self, values: list[Any | None | NotNone]) -> SqlFieldBuilder:
        self._is_filter = True
        self._filter_values = values

        return self

    def as_fixed(self, value: Any | None) -> SqlFieldBuilder:
        self._is_fixed = True
        self._fixed_value = value

        return self

    def build(self) -> _SqlField:
        return _SqlField(
            name=self._name,
            is_id=self._is_id,
            is_selectable=self._is_selectable,
            is_composite=self._is_composite,
            include_in_insert=self._include_in_insert,
            include_in_update=self._include_in_update,
            is_ordered=self._is_ordered,
            is_descending=self._is_descending,
            is_parent=self._is_parent,
            parent_value=self._parent_value,
            is_filter=self._is_filter,
            filter_values=self._filter_values,
            is_fixed=self._is_fixed,
            fixed_value=self._fixed_value,
        )


@dataclass
class SqlFieldManager:
    fields: list[_SqlField]
    custom_filters: list[str]
    key_formatter: str
    value_formatter: str

    @property
    def id(self) -> str:
        result = next((key for key in self.fields if key.is_id), None)
        if result is None:
            raise ValueError("Id field is required.")
        return result.name

    @property
    def composite(self) -> list[str]:
        names = [key.name for key in self.fields if key.is_composite]
        return [self.id] if len(names) == 0 else names

    @property
    def order(self) -> str:
        ordering = [key for key in self.fields if key.is_ordered]
        order_clauses = [
            f"{key.name} DESC" if key.is_descending else key.name for key in ordering
        ]
        if len(ordering) > 0:
            return "ORDER BY " + ", ".join(order_clauses)

        return ""

    def __iter__(self) -> Iterator[_SqlField]:
        yield from self.fields

    def where_statement(self, include_id: bool = False, read_id: bool = False) -> str:
        statements = [
            statement
            for statement in [
                self._parent_filter(),
                self._id_filter(include_id, read_id),
                self._general_filters(),
            ]
            if statement != ""
        ]
        if len(statements) > 0:
            return "WHERE " + " AND ".join(statements)

        return ""

    def with_fixed(self, raw: Mapping[str, Any]) -> dict[str, Any]:
        data = dict(raw)

        for key in self.fields:
            if key.is_parent:
                data[key.name] = key.parent_value
            if key.is_fixed:
                data[key.name] = key.fixed_value
            if key.is_filter:
                for index, value in enumerate(key.filter_values):
                    if value is not None and not isinstance(value, NotNone):
                        data[key.name + "_filter_" + str(index)] = value
        return data

    def _parent_filter(self) -> str:
        result = next((key for key in self.fields if key.is_parent), None)
        if result is not None:
            if result.parent_value is None:
                return self.key_formatter.replace("x", result.name) + " IS NULL"
            return (
                self.key_formatter.replace("x", result.name)
                + " = "
                + self.value_formatter.replace("x", result.name)
            )

        return ""

    def _id_filter(self, include_id: bool, read_id: bool) -> str:
        if not include_id:
            return ""

        clauses = []

        id_field = next((key for key in self.fields if key.is_id), None)
        if id_field is None:
            raise ValueError("Id field is required.")

        value_expr = (
            self.value_formatter.replace("x", id_field.name)
            if not read_id or id_field.include_in_insert
            else "SCOPE_IDENTITY()"
        )
        clauses.append(
            f"{self.key_formatter.replace('x', id_field.name)} = {value_expr}"
        )

        if not read_id:
            selectable_fields = [
                selectable
                for selectable in self.fields
                if selectable.is_selectable and not selectable.is_id
            ]
            for selectable in selectable_fields:
                key_expr = self.key_formatter.replace("x", selectable.name)
                val_expr = self.value_formatter.replace("x", id_field.name)
                clauses.append(f"{key_expr} = {val_expr}")

        if len(clauses) == 1:
            return clauses[0]

        return "(" + " OR ".join(clauses) + ")"

    def _general_filters(self) -> str:
        statements: list[str] = [] + self.custom_filters
        for key in self.fields:
            if key.is_filter:
                inner_statements: list[str] = []
                for index, value in enumerate(key.filter_values):
                    if value is None:
                        inner_statements.append(
                            self.key_formatter.replace("x", key.name) + " IS NULL"
                        )
                    elif isinstance(value, NotNone):
                        inner_statements.append(
                            self.key_formatter.replace("x", key.name) + " IS NOT NULL"
                        )
                    else:
                        inner_statements.append(
                            self.key_formatter.replace("x", key.name)
                            + " = "
                            + self.value_formatter.replace(
                                "x", key.name + "_filter_" + str(index)
                            )
                        )
                if len(inner_statements) > 0:
                    statements.append("(" + " OR ".join(inner_statements) + ")")

        return " AND ".join(statements)

    @dataclass
    class Builder:
        custom_filters: list[str] = field(default_factory=list)

        fields: list[_SqlField] = field(init=False)
        key_formatter: str = field(init=False)
        value_formatter: str = field(init=False)

        def with_fields(self, fields: list[_SqlField]) -> SqlFieldManager.Builder:
            self.fields = fields

            return self

        def with_custom_filters(self, fields: list[str]) -> SqlFieldManager.Builder:
            self.custom_filters = fields

            return self

        def for_sqlite(self) -> SqlFieldManager.Builder:
            self.key_formatter = "x"
            self.value_formatter = ":x"

            return self

        def for_mssql(self) -> SqlFieldManager.Builder:
            self.key_formatter = "[x]"
            self.value_formatter = "%(x)s"

            return self

        def build(self) -> SqlFieldManager:
            return SqlFieldManager(
                self.fields,
                self.custom_filters,
                self.key_formatter,
                self.value_formatter,
            )

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterator


@dataclass(frozen=True)
class NotNone:
    pass


@dataclass(frozen=True)
class _SqlField:
    name: str
    is_id: bool = False
    is_ordered: bool = False
    is_composite: bool = False
    include_in_insert: bool = True
    include_in_update: bool = True

    is_parent: bool = False
    parent_value: Any | None = None

    is_filter: bool = False
    filter_value: Any | None | NotNone = None

    is_fixed: bool = False
    fixed_value: Any | None = None


@dataclass
class SqlFieldBuilder:
    _name: str = field(init=False)
    _is_id: bool = False
    _is_ordered: bool = False
    _is_composite: bool = False
    _include_in_insert: bool = True
    _include_in_update: bool = True

    _is_parent: bool = False
    _parent_value: Any | None = None

    _is_filter: bool = False
    _filter_value: Any | None | NotNone = None

    _is_fixed: bool = False
    _fixed_value: Any | None = None

    def with_name(self, value: str) -> SqlFieldBuilder:
        self._name = value

        return self

    def as_id(self) -> SqlFieldBuilder:
        self._is_id = True

        return self

    def as_composite(self) -> SqlFieldBuilder:
        self._is_composite = True

        return self

    def in_ordering(self) -> SqlFieldBuilder:
        self._is_ordered = True

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

    def as_filter(self, value: Any | None | NotNone) -> SqlFieldBuilder:
        self._is_filter = True
        self._filter_value = value

        return self

    def as_fixed(self, value: Any | None) -> SqlFieldBuilder:
        self._is_fixed = True
        self._fixed_value = value

        return self

    def build(self) -> _SqlField:
        return _SqlField(
            self._name,
            self._is_id,
            self._is_ordered,
            self._is_composite,
            self._include_in_insert,
            self._include_in_update,
            self._is_parent,
            self._parent_value,
            self._is_filter,
            self._filter_value,
            self._is_fixed,
            self._fixed_value,
        )


@dataclass
class SqlFieldManager:
    fields: list[_SqlField]
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
        ordering = [key.name for key in self.fields if key.is_ordered]
        if len(ordering) > 0:
            return "ORDER BY " + ", ".join(ordering)
        else:
            return ""

    def __iter__(self) -> Iterator[_SqlField]:
        yield from self.fields

    def where_statement(self, include_id: bool = False) -> str:
        statements = [
            statement
            for statement in [
                self._parent_filter(),
                self._id_filter(include_id),
                self._general_filters(),
            ]
            if statement != ""
        ]
        if len(statements) > 0:
            return "WHERE " + " AND ".join(statements)
        else:
            return ""

    def with_fixed(self, data: dict[str, Any]) -> dict[str, Any]:
        for key in self.fields:
            if key.is_parent:
                data[key.name] = key.parent_value
            if key.is_fixed:
                data[key.name] = key.fixed_value
        return data

    def _parent_filter(self) -> str:
        result = next((key for key in self.fields if key.is_parent), None)
        if result is not None:
            if result.parent_value is None:
                return self.key_formatter.replace("x", result.name) + " IS NULL"
            else:
                return (
                    self.key_formatter.replace("x", result.name)
                    + " = "
                    + self.value_formatter.replace("x", result.name)
                )
        else:
            return ""

    def _id_filter(self, include_id: bool = False) -> str:
        return (
            self.key_formatter.replace("x", self.id)
            + " = "
            + self.value_formatter.replace("x", self.id)
            if include_id
            else ""
        )

    def _general_filters(self) -> str:
        statements: list[str] = []
        for key in self.fields:
            if key.is_filter:
                if key.filter_value is None:
                    statements.append(
                        self.key_formatter.replace("x", key.name) + " IS NULL"
                    )
                elif isinstance(key.filter_value, NotNone):
                    statements.append(
                        self.key_formatter.replace("x", key.name) + " IS NOT NULL"
                    )
                else:
                    statements.append(
                        self.key_formatter.replace("x", key.name)
                        + " = "
                        + self.value_formatter.replace("x", key.name)
                    )

        return " AND ".join(statements)

    @dataclass
    class Builder:
        fields: list[_SqlField] = field(init=False)
        key_formatter: str = field(init=False)
        value_formatter: str = field(init=False)

        def with_fields(self, fields: list[_SqlField]) -> SqlFieldManager.Builder:
            self.fields = fields

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
                self.fields, self.key_formatter, self.value_formatter
            )

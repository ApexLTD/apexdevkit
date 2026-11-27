from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Mapping


@dataclass(frozen=True)
class NotNone:
    pass


@dataclass(frozen=True)
class SqlField:
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
    filter_values: list[Any | NotNone | None] = field(default_factory=list)

    is_fixed: bool = False
    fixed_value: Any | None = None

    @classmethod
    def named(cls, name: str) -> Self:
        return cls(name=name)

    def as_id(self) -> Self:
        return replace(self, is_id=True)

    def selectable(self) -> Self:
        return replace(self, is_selectable=True)

    def composite(self) -> Self:
        return replace(self, is_composite=True)

    def order_by(self, *, descending: bool = False) -> Self:
        return replace(self, is_ordered=True, is_descending=descending)

    def derive_on_insert(self) -> Self:
        return replace(self, include_in_insert=False)

    def not_editable(self) -> Self:
        return replace(self, include_in_update=False)

    def parent(self, value: Any | None) -> Self:
        return replace(self, is_parent=True, parent_value=value)

    def filter(self, values: list[Any | NotNone | None]) -> Self:
        return replace(self, is_filter=True, filter_values=values)

    def fixed(self, value: Any | None) -> Self:
        return replace(self, is_fixed=True, fixed_value=value)


@dataclass(frozen=True)
class SqlFieldSet:
    items: list[SqlField] = field(default_factory=list)

    def __iter__(self) -> Iterator[SqlField]:
        return iter(self.items)

    @property
    def id_field(self) -> SqlField:
        for item in self.items:
            if item.is_id:
                return item

        raise RuntimeError("FieldSet does not contain Id field.")

    def contains_id(self) -> bool:
        return any(i.is_id for i in self.items)

    def add(self, item: SqlField) -> Self:
        self.items.append(self.validate(item))

        return self

    def validate(self, item: SqlField) -> SqlField:
        if item.is_id and self.contains_id():
            raise ValueError("Pass only one identifier key.")

        if item.is_parent and any(i.is_parent for i in self.items):
            raise ValueError("Pass only one parent key.")

        if not item.is_filter and isinstance(item.fixed_value, NotNone):
            raise ValueError("Only filter fields can be 'not null'.")

        return item

    def for_ordering(self) -> Iterable[SqlField]:
        return (item for item in self.items if item.is_ordered)

    def for_filtering(self) -> Iterable[SqlField]:
        return (item for item in self.items if item.is_filter)


@dataclass
class SqlFieldManager:
    fields: SqlFieldSet
    custom_filters: list[str]

    placeholder_value: PlaceHolder
    placeholder_key: PlaceHolder

    @property
    def id_name(self) -> str:
        return self.fields.id_field.name

    @property
    def composite(self) -> list[str]:
        names = [key.name for key in self.fields if key.is_composite]

        return [self.id_name] if len(names) == 0 else names

    @property
    def order(self) -> str:
        fields = [
            f"{item.name} DESC" if item.is_descending else item.name
            for item in self.fields.for_ordering()
        ]

        if not fields:
            return ""

        return "ORDER BY " + ", ".join(fields)

    def __iter__(self) -> Iterator[SqlField]:
        yield from self.fields

    def where_statement(
        self,
        *,
        include_id: bool = False,
        read_id: bool = False,
    ) -> str:
        statements = [
            statement
            for statement in [
                self._parent_filter(),
                self._id_filter(include_id=include_id, read_id=read_id),
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

        if result is None:
            return ""

        if result.parent_value is None:
            return self.placeholder_key.is_null(result.name)

        return (
            self.placeholder_key.replace_with(result.name)
            + " = "
            + self.placeholder_value.replace_with(result.name)
        )

    def _id_filter(self, *, include_id: bool, read_id: bool) -> str:
        if not include_id:
            return ""

        id_field = self.fields.id_field

        value_expr = (
            self.placeholder_value.replace_with(id_field.name)
            if not read_id or id_field.include_in_insert
            else "SCOPE_IDENTITY()"
        )

        clauses = [
            f"{self.placeholder_key.replace_with(id_field.name)} = {value_expr}",
        ]

        if not read_id:
            selectable_fields = [
                selectable
                for selectable in self.fields
                if selectable.is_selectable and not selectable.is_id
            ]
            for selectable in selectable_fields:
                key_expr = self.placeholder_key.replace_with(selectable.name)
                val_expr = self.placeholder_value.replace_with(id_field.name)
                clauses.append(f"{key_expr} = {val_expr}")

        if len(clauses) == 1:
            return clauses[0]

        return "(" + " OR ".join(clauses) + ")"

    def _general_filters(self) -> str:
        statements: list[str] = [*self.custom_filters]
        for item in self.fields.for_filtering():
            name = item.name

            inner = [
                self.filter_with_a(name, value, index)
                for index, value in enumerate(item.filter_values)
            ]

            if len(inner) > 0:
                statements.append("(" + " OR ".join(inner) + ")")

        return " AND ".join(statements)

    def filter_with_a(self, name: str, value: Any | NotNone | None, index: int) -> str:
        if value is None:
            return self.placeholder_key.is_null(name)

        if isinstance(value, NotNone):
            return self.placeholder_key.is_not_null(name)

        return (
            self.placeholder_key.replace_with(name)
            + " = "
            + self.placeholder_value.replace_with(name + "_filter_" + str(index))
        )

    @dataclass
    class Builder:
        placeholder_value: PlaceHolder
        placeholder_key: PlaceHolder

        fields: SqlFieldSet = field(default_factory=SqlFieldSet)
        custom_filters: list[str] = field(default_factory=list)

        @classmethod
        def for_sqlite(cls) -> Self:
            return cls(
                placeholder_key=SqliteKeyPlaceholder(),
                placeholder_value=SqliteValuePlaceholder(),
            )

        @classmethod
        def for_mssql(cls) -> Self:
            return cls(
                placeholder_key=MsSqlKeyPlaceholder(),
                placeholder_value=MsSqlValuePlaceholder(),
            )

        def with_fields(self, fields: SqlFieldSet) -> Self:
            self.fields = fields

            return self

        def with_custom_filters(self, fields: list[str]) -> Self:
            self.custom_filters = fields

            return self

        def build(self) -> SqlFieldManager:
            return SqlFieldManager(
                fields=self.fields,
                custom_filters=self.custom_filters,
                placeholder_value=self.placeholder_value,
                placeholder_key=self.placeholder_key,
            )


class PlaceHolder(ABC):
    def is_null(self, value: str) -> str:
        return self.replace_with(value) + " IS NULL"

    def is_not_null(self, value: str) -> str:
        return self.replace_with(value) + " IS NOT NULL"

    @abstractmethod
    def replace_with(self, value: str) -> str:
        pass


@dataclass(frozen=True)
class MsSqlKeyPlaceholder(PlaceHolder):
    def replace_with(self, value: str) -> str:
        return f"[{value}]"


@dataclass(frozen=True)
class MsSqlValuePlaceholder(PlaceHolder):
    def replace_with(self, value: str) -> str:
        return f"%({value})s"


@dataclass(frozen=True)
class SqliteKeyPlaceholder(PlaceHolder):
    def replace_with(self, value: str) -> str:
        return f"{value}"


@dataclass(frozen=True)
class SqliteValuePlaceholder(PlaceHolder):
    def replace_with(self, value: str) -> str:
        return f":{value}"

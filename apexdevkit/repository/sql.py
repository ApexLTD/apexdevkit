from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


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
            self._is_parent,
            self._parent_value,
            self._is_filter,
            self._filter_value,
            self._is_fixed,
            self._fixed_value,
        )

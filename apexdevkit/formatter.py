from __future__ import annotations

import pickle
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import asdict, dataclass, field, fields, is_dataclass
from typing import Any, Generic, Protocol, Self, TypeVar, get_args, get_type_hints

from apexdevkit.fluent import FluentDict
from apexdevkit.value import Value

_SourceT = TypeVar("_SourceT")
_TargetT = TypeVar("_TargetT")
_ItemT = TypeVar("_ItemT")


class Formatter(Protocol[_SourceT, _TargetT]):  # pragma: no cover
    def load(self, source: _SourceT) -> _TargetT:
        pass

    def dump(self, target: _TargetT) -> _SourceT:
        pass


@dataclass(frozen=True)
class AliasFormatter(Formatter[Mapping[str, Any], _TargetT]):
    inner: Formatter[Mapping[str, Any], _TargetT]

    alias: AliasMapping

    def load(self, source: Mapping[str, Any]) -> _TargetT:
        return self.inner.load(self.alias.reverse().translate(source))

    def dump(self, target: _TargetT) -> Mapping[str, Any]:
        return self.alias.translate(self.inner.dump(target))


@dataclass(frozen=True)
class AliasMapping:
    alias: Mapping[str, str]

    @classmethod
    def parse(cls, **alias: str) -> AliasMapping:
        return cls(alias)

    def reverse(self) -> AliasMapping:
        return AliasMapping({value: key for key, value in self.alias.items()})

    def translate(self, mapping: Mapping[str, Any]) -> Mapping[str, Any]:
        return {self.value_of(key): value for key, value in mapping.items()}

    def value_of(self, key: str) -> str:
        return self.alias.get(key, key)


class PickleFormatter(Generic[_ItemT]):
    def dump(self, item: _ItemT) -> bytes:
        return pickle.dumps(item)

    def load(self, raw: bytes) -> _ItemT:
        return pickle.loads(raw)  # type: ignore


@dataclass
class ListFormatter(Generic[_SourceT, _TargetT]):
    inner: Formatter[_SourceT, _TargetT]

    def load(self, source: list[_SourceT]) -> list[_TargetT]:
        return [self.inner.load(item) for item in source]

    def dump(self, target: list[_TargetT]) -> list[_SourceT]:
        return [self.inner.dump(item) for item in target]


@dataclass
class DataclassFormatter(Generic[_TargetT]):
    resource: type[_TargetT]
    sub_formatters: dict[str, Formatter[Any, Any]] = field(default_factory=dict)

    def and_nested(self, **formatters: Formatter[Any, Any]) -> Self:
        return self.with_nested(**formatters)

    def with_nested(self, **formatters: Formatter[Any, Any]) -> Self:
        self.sub_formatters.update(formatters)

        return self

    def load(self, raw: Mapping[str, Any]) -> _TargetT:
        raw = FluentDict[Any](deepcopy(raw)).select(
            *self.resource.__annotations__.keys()
        )

        for key in fields(self.resource):  # type: ignore
            types = get_type_hints(self.resource)
            key_type = types[key.name]
            if key.name not in raw:
                continue
            if key.name in self.sub_formatters:
                raw[key.name] = (
                    self.sub_formatters[key.name].load(raw.pop(key.name))
                    if raw[key.name]
                    else raw[key.name]
                )
            elif is_dataclass(key_type):
                raw[key.name] = DataclassFormatter(key_type).load(raw[key.name])  # type: ignore
            else:
                args = get_args(key_type)
                if len(args) == 1 and is_dataclass(args[0]):
                    raw[key.name] = ListFormatter(DataclassFormatter(args[0])).load(  # type: ignore
                        raw[key.name]
                    )

        return self.resource(**raw)

    def dump(self, item: _TargetT) -> Mapping[str, Any]:
        return asdict(item)  # type: ignore


class ValueFormatter:
    def load(self, raw: Mapping[str, Any]) -> Value:
        return DataclassFormatter(Value).load(raw)

    def dump(self, value: Value) -> Mapping[str, Any]:
        return DataclassFormatter(Value).dump(value)

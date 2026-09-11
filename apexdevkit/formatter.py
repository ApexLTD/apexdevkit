from __future__ import annotations

import pickle
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import asdict, dataclass, field, fields, is_dataclass
from typing import Any, Protocol, Self, get_args, get_type_hints

from pypebbles import FluentDict


class Formatter[SourceT, TargetT](Protocol):  # pragma: no cover
    def load(self, source: SourceT) -> TargetT:
        pass

    def dump(self, target: TargetT) -> SourceT:
        pass


@dataclass(frozen=True)
class AliasFormatter[TargetT](Formatter[Mapping[str, Any], TargetT]):
    inner: Formatter[Mapping[str, Any], TargetT]

    alias: AliasMapping

    def load(self, source: Mapping[str, Any]) -> TargetT:
        return self.inner.load(self.alias.reverse().translate(source))

    def dump(self, target: TargetT) -> Mapping[str, Any]:
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


class PickleFormatter[ItemT]:
    def dump(self, item: ItemT) -> bytes:
        return pickle.dumps(item)

    def load(self, raw: bytes) -> ItemT:
        return pickle.loads(raw)  # type: ignore


@dataclass
class ListFormatter[SourceT, TargetT]:
    inner: Formatter[SourceT, TargetT]

    def load(self, source: list[SourceT]) -> list[TargetT]:
        return [self.inner.load(item) for item in source]

    def dump(self, target: list[TargetT]) -> list[SourceT]:
        return [self.inner.dump(item) for item in target]


@dataclass
class DataclassFormatter[TargetT]:
    resource: type[TargetT]
    sub_formatters: dict[str, Formatter[Any, Any]] = field(default_factory=dict)

    def and_nested(self, **formatters: Formatter[Any, Any]) -> Self:
        return self.with_nested(**formatters)

    def with_nested(self, **formatters: Formatter[Any, Any]) -> Self:
        self.sub_formatters.update(formatters)

        return self

    def load(self, source: Mapping[str, Any]) -> TargetT:
        source = FluentDict[Any](deepcopy(source)).select(
            *self.resource.__annotations__.keys(),
            "id",
            "idempotency_id",
        )

        for key in fields(self.resource):  # type: ignore
            types = get_type_hints(self.resource)
            key_type = types[key.name]
            if key.name not in source:
                continue
            if key.name in self.sub_formatters:
                source[key.name] = (
                    self.sub_formatters[key.name].load(source.pop(key.name))
                    if source[key.name]
                    else source[key.name]
                )
            elif is_dataclass(key_type):
                source[key.name] = DataclassFormatter(key_type).load(source[key.name])  # type: ignore
            else:
                args = get_args(key_type)
                if len(args) == 1 and is_dataclass(args[0]):
                    source[key.name] = ListFormatter(DataclassFormatter(args[0])).load(  # type: ignore
                        source[key.name]
                    )

        return self.resource(**source)

    def dump(self, target: TargetT) -> Mapping[str, Any]:
        return asdict(target)  # type: ignore

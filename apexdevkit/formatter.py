from copy import deepcopy
from dataclasses import asdict, dataclass, field
from typing import Any, Generic, Protocol, Self, TypeVar

_SourceT = TypeVar("_SourceT")
_TargetT = TypeVar("_TargetT")


class Formatter(Protocol[_SourceT, _TargetT]):  # pragma: no cover
    def load(self, raw: _SourceT) -> _TargetT:
        pass

    def dump(self, item: _TargetT) -> _SourceT:
        pass


@dataclass
class ListFormatter(Generic[_TargetT, _SourceT]):
    inner: Formatter[_SourceT, _TargetT]

    def load(self, raw: list[_SourceT]) -> list[_TargetT]:
        result = []
        for item in raw:
            result.append(self.inner.load(item))
        return result

    def dump(self, items: list[_TargetT]) -> list[_SourceT]:
        result: list[_SourceT] = []
        for item in items:
            result.append(self.inner.dump(item))
        return result


@dataclass
class DataclassFormatter(Generic[_TargetT]):
    resource: type[_TargetT]
    sub_formatters: dict[str, Formatter[Any, Any]] = field(default_factory=dict)

    def and_nested(self, **formatters: Formatter[Any, Any]) -> Self:
        return self.with_nested(**formatters)

    def with_nested(self, **formatters: Formatter[Any, Any]) -> Self:
        self.sub_formatters.update(formatters)

        return self

    def load(self, raw: dict[str, Any]) -> _TargetT:
        raw = deepcopy(raw)

        for key, formatter in self.sub_formatters.items():
            raw[key] = formatter.load(raw.pop(key))

        return self.resource(**raw)

    def dump(self, item: _TargetT) -> dict[str, Any]:
        return asdict(item)  # type: ignore

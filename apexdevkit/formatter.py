from copy import deepcopy
from dataclasses import asdict, dataclass, field
from typing import Any, Generic, Protocol, Self, TypeVar

ItemT = TypeVar("ItemT")


class Formatter(Protocol[ItemT]):  # pragma: no cover
    def load(self, raw: dict[str, Any]) -> ItemT:
        pass

    def dump(self, item: ItemT) -> dict[str, Any]:
        pass


@dataclass
class ListFormatter(Generic[ItemT]):
    inner: Formatter[ItemT]

    def load(self, raw: list[dict[str, Any]]) -> list[ItemT]:
        result = []
        for item in raw:
            result.append(self.inner.load(item))
        return result

    def dump(self, items: list[ItemT]) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for item in items:
            result.append(self.inner.dump(item))
        return result


@dataclass
class DataclassFormatter(Generic[ItemT]):
    resource: type[ItemT]
    sub_formatters: dict[str, Formatter[Any] | ListFormatter[Any]] = field(
        default_factory=dict
    )

    def and_nested(self, **formatters: Formatter[Any] | ListFormatter[Any]) -> Self:
        return self.with_nested(**formatters)

    def with_nested(self, **formatters: Formatter[Any] | ListFormatter[Any]) -> Self:
        self.sub_formatters.update(formatters)

        return self

    def load(self, raw: dict[str, Any]) -> ItemT:
        raw = deepcopy(raw)

        for key, formatter in self.sub_formatters.items():
            raw[key] = formatter.load(raw.pop(key))

        return self.resource(**raw)

    def dump(self, item: ItemT) -> dict[str, Any]:
        return asdict(item)  # type: ignore

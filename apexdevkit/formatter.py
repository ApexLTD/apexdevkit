from dataclasses import asdict, dataclass
from typing import Any, Generic, Protocol, TypeVar

ItemT = TypeVar("ItemT")


class Formatter(Protocol[ItemT]):
    def load(self, raw: dict[str, Any]) -> ItemT:
        pass

    def dump(self, item: ItemT) -> dict[str, Any]:
        pass


@dataclass
class DataclassFormatter(Generic[ItemT]):
    resource: type[ItemT]

    def load(self, raw: dict[str, Any]) -> ItemT:
        return self.resource(**raw)

    def dump(self, item: ItemT) -> dict[str, Any]:
        return asdict(item)  # type: ignore

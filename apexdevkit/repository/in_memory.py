from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Iterator, Self, Generic, Protocol

from apexdevkit.error import DoesNotExistError, ExistsError
from apexdevkit.formatter import Formatter
from apexdevkit.repository import RepositoryBase
from apexdevkit.repository.interface import ItemT

KeyFunction = Callable[[Any], str]
_Raw = dict[str, Any]


@dataclass
class AttributeKey:
    name: str

    def __call__(self, item: Any) -> str:
        return str(getattr(item, self.name))


@dataclass
class InMemoryRepository(RepositoryBase[ItemT]):
    formatter: Formatter[_Raw, ItemT]

    _keys: list[KeyFunction] = field(init=False, default_factory=list)

    def __post_init__(self) -> None:
        self.store = InMemoryKeyValueStore(self.formatter)

    def bind(self, **kwargs: Any) -> Self:
        return self

    def with_key(self, function: KeyFunction) -> Self:
        self._keys.append(function)

        return self

    def with_seeded(self, *items: ItemT) -> Self:
        for item in items:
            self.create(item)

        return self

    def create(self, item: ItemT) -> ItemT:
        self._ensure_does_not_exist(item)
        self.store.set(self._pk(item), item)

        return item

    def _ensure_does_not_exist(self, new: ItemT) -> None:
        for existing in self:
            error = ExistsError(existing)

            for key in self._keys:
                if key(new) == key(existing):
                    error.with_duplicate(key)

            error.fire()

    def _pk(self, item: ItemT) -> Any:
        return self._keys[0](item)

    def update(self, item: ItemT) -> None:
        self.delete(self._pk(item))
        self.create(item)

    def delete(self, item_id: str) -> None:
        item = self.read(item_id)
        self.store.drop(self._pk(item))

    def read(self, item_id: str) -> ItemT:
        for key in self._keys:
            for item in self:
                if key(item) == str(item_id):
                    return item

        raise DoesNotExistError(item_id)

    def __iter__(self) -> Iterator[ItemT]:
        return iter(self.store.values())

    def __len__(self) -> int:
        return self.store.count()


@dataclass
class KeyValueStore(Protocol[ItemT]):
    def count(self) -> int:
        pass

    def set(self, key: str, value: ItemT) -> None:
        pass

    def get(self, key: str) -> ItemT:
        pass

    def drop(self, key: str) -> None:
        pass

    def values(self) -> Iterable[ItemT]:
        pass


@dataclass
class InMemoryKeyValueStore(Generic[ItemT]):
    formatter: Formatter[_Raw, ItemT]

    items: dict[str, _Raw] = field(default_factory=dict)

    def count(self) -> int:
        return len(self.items)

    def set(self, key: str, value: ItemT) -> None:
        self.items[key] = self.formatter.dump(value)

    def get(self, key: str) -> ItemT:
        return self.formatter.load(self.items[key])

    def drop(self, key: str) -> None:
        del self.items[key]

    def values(self) -> Iterable[ItemT]:
        for raw in self.items.values():
            yield self.formatter.load(raw)

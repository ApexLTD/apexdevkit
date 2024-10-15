from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Generic, Iterable, Iterator, Protocol, Self

from apexdevkit.error import DoesNotExistError, ExistsError
from apexdevkit.formatter import Formatter, NoFormatter
from apexdevkit.key_fn import AttributeKey
from apexdevkit.repository import RepositoryBase
from apexdevkit.repository.interface import ItemT, Repository

KeyFunction = Callable[[Any], str]
_Raw = dict[str, Any]


@dataclass
class InMemoryRepository(Generic[ItemT]):
    store: KeyValueStore[ItemT] = field(default_factory=lambda: InMemoryKeyValueStore())
    keys: list[KeyFunction] = field(default_factory=list)
    seeds: list[ItemT] = field(default_factory=list)

    def with_formatter(self, value: Formatter[_Raw, ItemT]) -> Self:
        return self.with_store(InMemoryKeyValueStore(value))

    def with_store(self, value: KeyValueStore[ItemT]) -> Self:
        self.store = value

        return self

    def and_key(self, function: KeyFunction) -> Self:
        return self.with_key(function)

    def with_key(self, function: KeyFunction) -> Self:
        self.keys.append(function)

        return self

    def and_seeded(self, *items: ItemT) -> Self:
        return self.with_seeded(*items)

    def with_seeded(self, *items: ItemT) -> Self:
        self.seeds.extend(items)

        return self

    def build(self) -> Repository[ItemT]:
        return self._seed(self._create())

    def _seed(self, repository: Repository[ItemT]) -> Repository[ItemT]:
        for seed in self.seeds:
            repository.create(seed)

        return repository

    def _create(self) -> Repository[ItemT]:
        match len(self.keys):
            case 0:
                return _SingleKeyRepository(self.store, pk=AttributeKey("id"))
            case 1:
                return _SingleKeyRepository(self.store, pk=self.keys[0])
            case _:
                return _ManyKeyRepository(self.store, keys=self.keys)


class KeyValueStore(Protocol[ItemT]):  # pragma: no cover
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
    formatter: Formatter[_Raw, ItemT] = field(default_factory=NoFormatter)
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


@dataclass
class _SingleKeyRepository(RepositoryBase[ItemT]):
    store: KeyValueStore[ItemT]
    pk: KeyFunction

    def bind(self, **kwargs: Any) -> Self:  # pragma: no cover
        return self

    def create(self, item: ItemT) -> ItemT:
        self._ensure_does_not_exist(item)
        self.store.set(self.pk(item), item)

        return item

    def _ensure_does_not_exist(self, new: ItemT) -> None:
        try:
            existing = self.store.get(self.pk(new))
        except KeyError:
            return

        ExistsError(existing).with_duplicate(self.pk).fire()

    def update(self, item: ItemT) -> None:
        self.delete(self.pk(item))
        self.create(item)

    def delete(self, item_id: str) -> None:
        try:
            self.store.drop(item_id)
        except KeyError:
            raise DoesNotExistError(item_id)

    def read(self, item_id: str) -> ItemT:
        try:
            return self.store.get(item_id)
        except KeyError:
            raise DoesNotExistError(item_id)

    def __iter__(self) -> Iterator[ItemT]:
        return iter(self.store.values())

    def __len__(self) -> int:
        return self.store.count()


@dataclass
class _ManyKeyRepository(RepositoryBase[ItemT]):
    store: KeyValueStore[ItemT]

    keys: list[KeyFunction] = field(default_factory=list)

    def bind(self, **kwargs: Any) -> Self:  # pragma: no cover
        return self

    def create(self, item: ItemT) -> ItemT:
        self._ensure_does_not_exist(item)
        self.store.set(self._pk(item), item)

        return item

    def _ensure_does_not_exist(self, new: ItemT) -> None:
        for existing in self:
            error = ExistsError(existing)

            for key in self.keys:
                if key(new) == key(existing):
                    error.with_duplicate(key)

            error.fire()

    def _pk(self, item: ItemT) -> Any:
        return self.keys[0](item)

    def update(self, item: ItemT) -> None:
        self.delete(self._pk(item))
        self.create(item)

    def delete(self, item_id: str) -> None:
        item = self.read(item_id)
        self.store.drop(self._pk(item))

    def read(self, item_id: str) -> ItemT:
        for key in self.keys:
            for item in self:
                if key(item) == str(item_id):
                    return item

        raise DoesNotExistError(item_id)

    def __iter__(self) -> Iterator[ItemT]:
        return iter(self.store.values())

    def __len__(self) -> int:
        return self.store.count()

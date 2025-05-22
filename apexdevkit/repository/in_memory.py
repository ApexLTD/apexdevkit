from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable, Iterator, MutableMapping
from contextlib import suppress
from dataclasses import dataclass, field
from typing import Any, Generic, Protocol, Self

from apexdevkit.error import DoesNotExistError, ExistsError
from apexdevkit.formatter import Formatter, PickleFormatter
from apexdevkit.key_fn import AttributeKey
from apexdevkit.repository import RepositoryBase
from apexdevkit.repository.interface import ItemT, Repository

_KeyFunction = Callable[[ItemT], str]


@dataclass(frozen=True)
class InMemoryRepository(Generic[ItemT]):
    store: KeyValueStore[ItemT] = field(default_factory=lambda: InMemoryByteStore())
    keys: list[_KeyFunction[ItemT]] = field(default_factory=list)
    seeds: frozenset[ItemT] = field(default_factory=frozenset)

    def with_store(self, value: KeyValueStore[ItemT]) -> InMemoryRepository[ItemT]:
        return InMemoryRepository(store=value, keys=self.keys, seeds=self.seeds)

    def and_key(self, function: _KeyFunction[ItemT]) -> InMemoryRepository[ItemT]:
        return self.with_key(function)

    def with_key(self, function: _KeyFunction[ItemT]) -> InMemoryRepository[ItemT]:
        return InMemoryRepository(
            store=self.store,
            keys=[*self.keys, function],
            seeds=self.seeds,
        )

    def and_seeded(self, *items: ItemT) -> InMemoryRepository[ItemT]:
        return self.with_seeded(*items)

    def with_seeded(self, *items: ItemT) -> InMemoryRepository[ItemT]:
        return InMemoryRepository(
            store=self.store,
            keys=self.keys,
            seeds=self.seeds.union(set(items)),
        )

    def build(self) -> Repository[ItemT]:
        return self._seed(self._create())

    def _seed(self, repository: Repository[ItemT]) -> Repository[ItemT]:
        for seed in self.seeds:
            with suppress(ExistsError):
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
class InMemoryByteStore(Generic[ItemT]):
    formatter: Formatter[bytes, ItemT] = field(default_factory=PickleFormatter)

    items: dict[str, bytes] = field(default_factory=dict)

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
    class Cache:
        items: MutableMapping[str, InMemoryByteStore[Any]] = field(init=False)

        def __post_init__(self) -> None:
            self.items = defaultdict(InMemoryByteStore)

        def store_for(self, name: str) -> InMemoryByteStore[Any]:
            return self.items[name]

        def clear(self) -> None:
            self.items.clear()


@dataclass
class _SingleKeyRepository(RepositoryBase[ItemT]):
    store: KeyValueStore[ItemT]
    pk: _KeyFunction[ItemT]

    def bind(self, **_: Any) -> Self:  # pragma: no cover
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
        except KeyError as e:
            raise DoesNotExistError(item_id) from e

    def read(self, item_id: str) -> ItemT:
        try:
            return self.store.get(item_id)
        except KeyError as e:
            raise DoesNotExistError(item_id) from e

    def __iter__(self) -> Iterator[ItemT]:
        return iter(self.store.values())

    def __len__(self) -> int:
        return self.store.count()


@dataclass
class _ManyKeyRepository(RepositoryBase[ItemT]):
    store: KeyValueStore[ItemT]

    keys: list[_KeyFunction[ItemT]] = field(default_factory=list)

    def bind(self, **_: Any) -> Self:  # pragma: no cover
        return self

    def create(self, item: ItemT) -> ItemT:
        self._ensure_does_not_exist(item)
        self.store.set(self._pk(item), item)

        return item

    def _ensure_does_not_exist(self, new: ItemT) -> None:
        for existing in self:
            for key in self.keys:
                if key(new) == key(existing):
                    ExistsError(existing).with_duplicate(key).fire()

    def _pk(self, item: ItemT) -> str:
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

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Iterator, Self

from apexdevkit.error import DoesNotExistError, ExistsError
from apexdevkit.formatter import Formatter
from apexdevkit.repository import RepositoryBase
from apexdevkit.repository.interface import IdT, ItemT

KeyFunction = Callable[[Any], str]
_Raw = dict[str, Any]


@dataclass
class AttributeKey:
    name: str

    def __call__(self, item: Any) -> str:
        return str(getattr(item, self.name))


@dataclass
class InMemoryRepository(RepositoryBase[IdT, ItemT]):
    formatter: Formatter[_Raw, ItemT]
    items: dict[str, _Raw] = field(default_factory=dict)

    _keys: list[KeyFunction] = field(init=False, default_factory=list)

    def bind(self, **kwargs: Any) -> Self:
        return self

    def with_key(self, function: KeyFunction) -> Self:
        self._keys.append(function)

        return self

    def with_seeded(self, *items: ItemT) -> Self:
        self.create_many(list(items))

        return self

    def create_many(self, items: list[ItemT]) -> list[ItemT]:
        for item in items:
            self.create(item)

        return items

    def create(self, item: ItemT) -> ItemT:
        self._ensure_does_not_exist(item)
        self.items[self._pk(item)] = self.formatter.dump(item)

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

    def update_many(self, items: list[ItemT]) -> None:
        for item in items:
            self.update(item)

    def update(self, item: ItemT) -> None:
        self.delete(self._pk(item))
        self.create(item)

    def delete(self, item_id: IdT) -> None:
        item = self.read(item_id)
        del self.items[self._pk(item)]

    def read(self, item_id: IdT) -> ItemT:
        for key in self._keys:
            for item in self:
                if key(item) == str(item_id):
                    return item

        raise DoesNotExistError(item_id)

    def __iter__(self) -> Iterator[ItemT]:
        yield from [self.formatter.load(raw) for raw in self.items.values()]

    def __len__(self) -> int:
        return len(self.items)

    def search(self, **kwargs: Any) -> Iterable[ItemT]:
        items = []

        for item in self.items.values():
            if kwargs.items() <= item.items():
                items.append(self.formatter.load(item))

        return items

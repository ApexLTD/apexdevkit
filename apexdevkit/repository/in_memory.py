from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Callable, Generic, Iterable, Iterator, Self, TypeVar

from apexdevkit.error import DoesNotExistError, ExistsError
from apexdevkit.formatter import Formatter

KeyFunction = Callable[[Any], str]

ItemT = TypeVar("ItemT")
_Raw = dict[str, Any]


@dataclass
class AttributeKey:
    name: str

    def __call__(self, item: Any) -> str:
        return str(getattr(item, self.name))


@dataclass
class InMemoryRepository(Generic[ItemT]):
    formatter: Formatter[_Raw, ItemT]
    items: dict[str, _Raw] = field(default_factory=dict)

    _key_functions: list[KeyFunction] = field(init=False, default_factory=list)

    def with_key(self, function: KeyFunction) -> Self:
        self._key_functions.append(function)

        return self

    def with_seeded(self, *items: ItemT) -> Self:
        for item in items:
            self.create(item)
        return self

    def create_many(self, items: list[ItemT]) -> list[ItemT]:
        for item in items:
            self.create(item)

        return items

    def create(self, item: ItemT) -> ItemT:
        self._ensure_does_not_exist(item)
        self.items[self._key_functions[0](item)] = deepcopy(self.formatter.dump(item))

        return item

    def _ensure_does_not_exist(self, new: ItemT) -> None:
        for existing in self:
            error = ExistsError(existing)

            for key in self._key_functions:
                if key(new) == key(existing):
                    error.with_duplicate(key)

            error.fire()

    def read(self, item_id: Any) -> ItemT:
        for key in self._key_functions:
            for item in self:
                if key(item) == str(item_id):
                    return item

        raise DoesNotExistError(item_id)

    def update(self, item: ItemT) -> None:
        self.delete(self._key_functions[0](item))
        self.create(item)

    def update_many(self, items: list[ItemT]) -> None:
        for item in items:
            self.update(item)

    def delete(self, item_id: Any) -> None:
        for key in self._key_functions:
            for item in self:
                if key(item) == str(item_id):
                    del self.items[self._key_functions[0](item)]
                    return
        raise DoesNotExistError(item_id)

    def search(self, **kwargs: Any) -> Iterable[ItemT]:
        items = []

        for item in self.items.values():
            if kwargs.items() <= item.items():
                items.append(self.formatter.load(item))

        return items

    def __iter__(self) -> Iterator[ItemT]:
        yield from [self.formatter.load(deepcopy(raw)) for raw in self.items.values()]

    def __len__(self) -> int:
        return len(self.items)

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Callable, Generic, Iterable, Iterator, Protocol, Self, TypeVar

from apexdevkit.annotation import deprecated
from apexdevkit.error import DoesNotExistError, ExistsError
from apexdevkit.formatter import DataclassFormatter, Formatter


class _Item(Protocol):  # pragma: no cover
    @property
    def id(self) -> Any:
        pass


KeyFunction = Callable[[Any], str]

ItemT = TypeVar("ItemT", bound=_Item)
_Raw = dict[str, Any]


@dataclass
class AttributeKey:
    name: str

    def __call__(self, item: Any) -> str:
        return getattr(item, self.name)


@dataclass
class InMemoryRepository(Generic[ItemT]):
    formatter: Formatter[_Raw, ItemT]
    items: dict[str, _Raw] = field(default_factory=dict)

    _key_functions: list[KeyFunction] = field(init=False, default_factory=list)

    @classmethod
    def for_dataclass(cls, value: type[ItemT]) -> "InMemoryRepository[ItemT]":
        return cls(DataclassFormatter(value))

    def __post_init__(self) -> None:
        self._key_functions = [AttributeKey("id")]

    @deprecated(
        """
        .with_searchable() is deprecated. Use .with_key() instead.
        Instead of .with_searchable("code") use .with_key(AttributeKey("code"))
        """
    )
    def with_searchable(self, attribute: str) -> Self:
        return self.with_key(AttributeKey(attribute))

    @deprecated(
        """
        .with_unique() is deprecated. Use .with_key() instead.
        Instead of .with_unique(criteria) use .with_key(criteria)
        """
    )
    def with_unique(self, criteria: KeyFunction) -> Self:
        return self.with_key(criteria)

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
        self.items[str(item.id)] = deepcopy(self.formatter.dump(item))

        return item

    def _ensure_does_not_exist(self, new: ItemT) -> None:
        for existing in self:
            error = ExistsError(existing)

            for key in self._key_functions:
                if key(new) == key(existing):
                    error.with_duplicate(key)

            error.fire()

    def read(self, item_id: Any) -> ItemT:
        for item in self:
            for key in self._key_functions:
                if key(item) == item_id:
                    return item

        raise DoesNotExistError(item_id)

    def update(self, item: ItemT) -> None:
        self.delete(item.id)
        self.create(item)

    def update_many(self, items: list[ItemT]) -> None:
        for item in items:
            self.update(item)

    def delete(self, item_id: Any) -> None:
        try:
            del self.items[str(item_id)]
        except KeyError:
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

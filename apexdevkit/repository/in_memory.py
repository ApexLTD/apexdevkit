from copy import deepcopy
from dataclasses import asdict, dataclass, field
from typing import Any, Generic, Iterable, Iterator, Protocol, Self, TypeVar

from apexdevkit.error import Criteria, DoesNotExistError, ExistsError


class _Item(Protocol):
    @property
    def id(self) -> Any:
        pass


ItemT = TypeVar("ItemT", bound=_Item)


class _Formatter(Protocol[ItemT]):
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


@dataclass
class InMemoryRepository(Generic[ItemT]):
    formatter: _Formatter[ItemT]
    items: dict[str, dict[str, Any]] = field(default_factory=dict)

    _uniques: list[Criteria] = field(init=False, default_factory=list)
    _search_by: list[str] = field(init=False, default_factory=list)

    @classmethod
    def for_dataclass(cls, value: type[ItemT]) -> "InMemoryRepository[ItemT]":
        return cls(DataclassFormatter(value))

    def __post_init__(self) -> None:
        self._search_by = ["id", *self._search_by]

    def with_searchable(self, attribute: str) -> Self:
        self._search_by.append(attribute)

        return self

    def with_unique(self, criteria: Criteria) -> Self:
        self._uniques.append(criteria)

        return self

    def with_seeded(self, *items: ItemT) -> Self:
        for item in items:
            self.create(item)
        return self

    def create_many(self, items: list[ItemT]) -> None:
        for item in items:
            self.create(item)

    def create(self, item: ItemT) -> None:
        self._ensure_does_not_exist(item)
        self.items[str(item.id)] = deepcopy(self.formatter.dump(item))

    def _ensure_does_not_exist(self, new: ItemT) -> None:
        for existing in self:
            error = ExistsError(existing)

            for criteria in self._uniques:
                if criteria(new) == criteria(existing):
                    error.with_duplicate(criteria)

            error.fire()

        assert str(new.id) not in self.items, f"Item with id<{new.id}> already exists"

    def read(self, item_id: Any) -> ItemT:
        for item in self:
            for attribute in self._search_by:
                if getattr(item, attribute) == item_id:
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

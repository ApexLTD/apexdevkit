from collections.abc import Container, Iterable, Iterator
from contextlib import suppress
from dataclasses import dataclass, field

from apexdevkit.error import DoesNotExistError, ExistsError

from .interface import ItemT, Repository


class NoRepository(Repository[ItemT]):  # pragma: no cover
    def create(self, item: ItemT) -> ItemT:
        raise NotImplementedError

    def read(self, item_id: str) -> ItemT:
        raise NotImplementedError

    def update(self, item: ItemT) -> None:
        raise NotImplementedError

    def delete(self, item_id: str) -> None:
        raise NotImplementedError

    def __iter__(self) -> Iterator[ItemT]:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError

    def __contains__(self, item: object) -> bool:
        raise NotImplementedError


@dataclass(frozen=True, kw_only=True)
class RepositoryDecorator(Repository[ItemT]):  # pragma: no cover
    inner: Repository[ItemT] = field(default_factory=NoRepository)

    def create(self, item: ItemT) -> ItemT:
        return self.inner.create(item)

    def read(self, item_id: str) -> ItemT:
        return self.inner.read(item_id)

    def update(self, item: ItemT) -> None:
        self.inner.update(item)

    def delete(self, item_id: str) -> None:
        self.inner.delete(item_id)

    def __iter__(self) -> Iterator[ItemT]:
        return iter(self.inner)

    def __len__(self) -> int:
        return len(self.inner)

    def __contains__(self, item: object) -> bool:
        return item in self.inner


@dataclass(frozen=True, kw_only=True)
class BruteForceBatch(RepositoryDecorator[ItemT]):
    def load(self, source: Iterable[ItemT]) -> Iterable[ItemT]:
        for item in list(source):
            with suppress(ExistsError):
                yield self.inner.create(item)

    def prune(self, source: Container[ItemT]) -> Iterable[ItemT]:
        for item in list(self.inner):
            if item not in source:
                with suppress(DoesNotExistError):
                    self.inner.delete(item.id)
                    yield item

    def renew(self, source: Iterable[ItemT]) -> Iterable[ItemT]:
        for item in list(source):
            with suppress(DoesNotExistError):
                self.inner.update(item)
                yield item

    def create_many(self, items: Iterable[ItemT]) -> Iterable[ItemT]:
        return [self.inner.create(item) for item in items]

    def update_many(self, items: Iterable[ItemT]) -> None:
        for item in items:
            self.inner.update(item)

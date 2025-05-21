from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from typing import Generic, TypeVar

from apexdevkit.error import DoesNotExistError
from apexdevkit.formatter import Formatter
from apexdevkit.repository import Repository, RepositoryBase

ItemT = TypeVar("ItemT")


@dataclass(frozen=True)
class NoFormatter(Generic[ItemT]):
    def load(self, item: ItemT) -> ItemT:
        return item

    def dump(self, item: ItemT) -> ItemT:
        return item


@dataclass(frozen=True)
class MultipleRepository(RepositoryBase[ItemT]):
    repositories: list[_InnerRepository[ItemT]]

    def create(self, item: ItemT) -> ItemT:
        for repository in self.repositories:
            if repository.condition(item):
                return repository.formatter.load(
                    repository.inner.create(repository.formatter.dump(item))
                )

        raise RuntimeError("Can not create as no table was found")

    def read(self, item_id: str) -> ItemT:
        for repository in self.repositories:
            if item_id.startswith(repository.id_prefix):
                return repository.formatter.load(
                    repository.inner.read(item_id.removeprefix(repository.id_prefix))
                )

        raise DoesNotExistError(item_id)

    def update(self, item: ItemT) -> None:
        for repository in self.repositories:
            if repository.condition(item):
                return repository.inner.update(repository.formatter.dump(item))

        raise RuntimeError("Can not update as no table was found")

    def delete(self, item_id: str) -> None:
        for repository in self.repositories:
            if item_id.startswith(repository.id_prefix):
                return repository.inner.delete(
                    item_id.removeprefix(repository.id_prefix)
                )

        raise DoesNotExistError(item_id)

    def __iter__(self) -> Iterator[ItemT]:
        for repository in self.repositories:
            yield from [
                repository.formatter.load(item) for item in list(repository.inner)
            ]

    def __len__(self) -> int:
        return sum(len(repository.inner) for repository in self.repositories)


@dataclass(frozen=True)
class MultipleRepositoryBuilder(Generic[ItemT]):
    repositories: list[_InnerRepository[ItemT]] = field(default_factory=list)

    def with_repository(
        self,
        repository: Repository[ItemT],
        condition: Callable[[ItemT], bool] = lambda _: True,
        formatter: Formatter[ItemT, ItemT] | None = None,
        id_prefix: str = "",
    ) -> MultipleRepositoryBuilder[ItemT]:
        return MultipleRepositoryBuilder[ItemT](
            self.repositories
            + [
                _InnerRepository(
                    repository,
                    condition,
                    formatter or NoFormatter[ItemT](),
                    id_prefix,
                )
            ]
        )

    def and_repository(
        self,
        repository: Repository[ItemT],
        condition: Callable[[ItemT], bool] = lambda _: True,
        formatter: Formatter[ItemT, ItemT] | None = None,
        id_prefix: str = "",
    ) -> MultipleRepositoryBuilder[ItemT]:
        return self.with_repository(
            repository,
            condition,
            formatter or NoFormatter[ItemT](),
            id_prefix,
        )

    def build(self) -> MultipleRepository[ItemT]:
        return MultipleRepository[ItemT](self.repositories)


@dataclass(frozen=True)
class _InnerRepository(Generic[ItemT]):
    inner: Repository[ItemT]
    condition: Callable[[ItemT], bool] = lambda _: True
    formatter: Formatter[ItemT, ItemT] = field(
        default_factory=lambda: NoFormatter[ItemT]()
    )
    id_prefix: str = ""

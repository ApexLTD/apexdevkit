from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Generic, Iterator, TypeVar

from apexdevkit.error import DoesNotExistError
from apexdevkit.repository import Repository, RepositoryBase

ItemT = TypeVar("ItemT")


@dataclass(frozen=True)
class MultipleRepository(RepositoryBase[ItemT]):
    repositories: list[_InnerRepository[ItemT]]

    def create(self, item: ItemT) -> ItemT:
        for repository in self.repositories:
            if repository.condition(item):
                return repository.repository.create(item)

        raise RuntimeError("Can not create as no table was found")

    def read(self, item_id: str) -> ItemT:
        for repository in self.repositories:
            if item_id.startswith(repository.id_prefix):
                return repository.repository.read(item_id)

        raise DoesNotExistError(item_id)

    def update(self, item: ItemT) -> None:
        for repository in self.repositories:
            if repository.condition(item):
                return repository.repository.update(item)

        raise RuntimeError("Can not update as no table was found")

    def delete(self, item_id: str) -> None:
        for repository in self.repositories:
            if item_id.startswith(repository.id_prefix):
                return repository.repository.delete(item_id)

        raise DoesNotExistError(item_id)

    def __iter__(self) -> Iterator[ItemT]:
        for repository in self.repositories:
            yield from repository.repository

    def __len__(self) -> int:
        return sum(len(repository.repository) for repository in self.repositories)


@dataclass(frozen=True)
class MultipleRepositoryBuilder(Generic[ItemT]):
    repositories: list[_InnerRepository[ItemT]] = field(default_factory=list)

    def with_repository(
        self,
        repository: Repository[ItemT],
        condition: Callable[[ItemT], bool] = lambda item: True,
        id_prefix: str = "",
    ) -> MultipleRepositoryBuilder[ItemT]:
        return MultipleRepositoryBuilder[ItemT](
            self.repositories + [_InnerRepository(repository, condition, id_prefix)]
        )

    def and_repository(
        self,
        repository: Repository[ItemT],
        condition: Callable[[ItemT], bool] = lambda item: True,
        id_prefix: str = "",
    ) -> MultipleRepositoryBuilder[ItemT]:
        return self.with_repository(repository, condition, id_prefix)

    def build(self) -> MultipleRepository[ItemT]:
        return MultipleRepository[ItemT](self.repositories)


@dataclass(frozen=True)
class _InnerRepository(Generic[ItemT]):
    repository: Repository[ItemT]
    condition: Callable[[ItemT], bool] = lambda item: True
    id_prefix: str = ""

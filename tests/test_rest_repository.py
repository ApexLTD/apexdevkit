from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, Type
from uuid import uuid4

import pytest

from apexdevkit.fastapi.service import RestfulRepositoryBuilder, RestfulService
from apexdevkit.formatter import DataclassFormatter
from apexdevkit.repository import InMemoryRepository
from apexdevkit.testing.fake import FakeResource


@dataclass
class Animal:
    name: str
    age: int

    id: str = field(default_factory=lambda: str(uuid4()))


@dataclass
class FakeAnimal(FakeResource[Animal]):
    item_type: Type[Animal] = field(default=Animal)

    @cached_property
    def _raw(self) -> dict[str, Any]:
        return {
            "id": self.fake.uuid(),
            "name": self.fake.text(length=10),
            "age": self.fake.number(),
        }


@pytest.fixture
def repository() -> InMemoryRepository[Animal]:
    return InMemoryRepository[Animal](DataclassFormatter(Animal))


@pytest.fixture
def service(repository: InMemoryRepository[Animal]) -> RestfulService:
    return (
        RestfulRepositoryBuilder[Animal]()
        .with_formatter(DataclassFormatter(Animal))
        .with_repository(repository)
        .build()
    )


def test_should_create_one(
    repository: InMemoryRepository[Animal], service: RestfulService
) -> None:
    animal = FakeAnimal()

    assert service.create_one(animal.json()) == animal.json()
    assert repository.read(animal.entity().id) == animal.entity()


def test_should_not_create_one(
    repository: InMemoryRepository[Animal], service: RestfulService
) -> None:
    animal = FakeAnimal()
    repository.create(animal.entity())

    with pytest.raises(AssertionError):
        service.create_one(animal.json())

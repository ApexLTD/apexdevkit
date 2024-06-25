from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, Type
from uuid import uuid4

import pytest

from apexdevkit.error import DoesNotExistError
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
    id: str | None = None
    name: str | None = None
    item_type: Type[Animal] = field(default=Animal)

    @cached_property
    def _raw(self) -> dict[str, Any]:
        return {
            "id": self.id or self.fake.uuid(),
            "name": self.name or self.fake.text(length=10),
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


def test_should_create_many(
    repository: InMemoryRepository[Animal], service: RestfulService
) -> None:
    animal_1 = FakeAnimal()
    animal_2 = FakeAnimal()

    assert service.create_many([animal_1.json(), animal_2.json()]) == [
        animal_1.json(),
        animal_2.json(),
    ]
    assert list(repository) == [animal_1.entity(), animal_2.entity()]


def test_should_not_create_many(
    repository: InMemoryRepository[Animal], service: RestfulService
) -> None:
    animal_1 = FakeAnimal()
    animal_2 = FakeAnimal()
    repository.create(animal_1.entity())

    with pytest.raises(AssertionError):
        service.create_many([animal_1.json(), animal_2.json()])


def test_should_read_one(
    repository: InMemoryRepository[Animal], service: RestfulService
) -> None:
    animal = FakeAnimal()
    repository.create(animal.entity())

    assert service.read_one(animal.entity().id) == animal.json()


def test_should_not_read_unknown(service: RestfulService) -> None:
    animal = FakeAnimal()

    with pytest.raises(DoesNotExistError):
        service.read_one(animal.entity().id)


def test_should_read_all(
    repository: InMemoryRepository[Animal], service: RestfulService
) -> None:
    animal_1 = FakeAnimal()
    animal_2 = FakeAnimal()
    repository.create_many([animal_1.entity(), animal_2.entity()])

    assert service.read_all() == [animal_1.json(), animal_2.json()]


def test_should_update_one(
    repository: InMemoryRepository[Animal], service: RestfulService
) -> None:
    initial = FakeAnimal().entity()
    updated = FakeAnimal(id=initial.id, name=initial.name)
    repository.create(initial)

    assert (
        service.update_one(updated.entity().id, age=updated.entity().age)
        == updated.json()
    )
    assert repository.read(updated.entity().id) == updated.entity()


def test_should_not_update_unknown(
    repository: InMemoryRepository[Animal], service: RestfulService
) -> None:
    updated = FakeAnimal()

    with pytest.raises(DoesNotExistError):
        service.update_one(updated.entity().id, age=updated.entity().age)


def test_should_update_many(
    repository: InMemoryRepository[Animal], service: RestfulService
) -> None:
    initial_1 = FakeAnimal().entity()
    initial_2 = FakeAnimal().entity()
    updated_1 = FakeAnimal(id=initial_1.id, name=initial_1.name)
    updated_2 = FakeAnimal(id=initial_2.id, name=initial_2.name)
    repository.create_many([initial_1, initial_2])

    assert service.update_many(
        [updated_1.json().drop("name"), updated_2.json().drop("name")]  # type: ignore
    ) == [updated_1.json(), updated_2.json()]
    assert list(repository) == [updated_1.entity(), updated_2.entity()]


def test_should_not_update_unknown_many(
    repository: InMemoryRepository[Animal], service: RestfulService
) -> None:
    updated_1 = FakeAnimal()
    updated_2 = FakeAnimal()

    with pytest.raises(DoesNotExistError):
        service.update_many(
            [updated_1.json().drop("name"), updated_2.json().drop("name")]  # type: ignore
        )


def test_should_replace_one(
    repository: InMemoryRepository[Animal], service: RestfulService
) -> None:
    initial = FakeAnimal().entity()
    replaced = FakeAnimal(id=initial.id)
    repository.create(initial)

    assert service.replace_one(replaced.json()) == replaced.json()
    assert repository.read(replaced.entity().id) == replaced.entity()


def test_should_not_replace_unknown(
    repository: InMemoryRepository[Animal], service: RestfulService
) -> None:
    replaced = FakeAnimal()

    with pytest.raises(DoesNotExistError):
        service.replace_one(replaced.json())


def test_should_replace_many(
    repository: InMemoryRepository[Animal], service: RestfulService
) -> None:
    initial_1 = FakeAnimal().entity()
    initial_2 = FakeAnimal().entity()
    replaced_1 = FakeAnimal(id=initial_1.id)
    replaced_2 = FakeAnimal(id=initial_2.id)
    repository.create_many([initial_1, initial_2])

    assert service.replace_many([replaced_1.json(), replaced_2.json()]) == [
        replaced_1.json(),
        replaced_2.json(),
    ]
    assert list(repository) == [replaced_1.entity(), replaced_2.entity()]


def test_should_not_replace_unknown_many(
    repository: InMemoryRepository[Animal], service: RestfulService
) -> None:
    replaced_1 = FakeAnimal()
    replaced_2 = FakeAnimal()

    with pytest.raises(DoesNotExistError):
        service.replace_many([replaced_1.json(), replaced_2.json()])

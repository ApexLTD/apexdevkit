from dataclasses import dataclass, field
from functools import cached_property
from typing import Any

import pytest

from apexdevkit.error import DoesNotExistError, ExistsError
from apexdevkit.fastapi.service import (
    RestfulRepository,
    RestfulServiceShell,
)
from apexdevkit.formatter import DataclassFormatter
from apexdevkit.repository import (
    Entity,
    InMemoryByteStore,
    InMemoryRepository,
    Repository,
)
from tests.fake import FakeResource


@dataclass(frozen=True, kw_only=True)
class Animal(Entity):
    name: str
    age: int


@dataclass(frozen=True)
class FakeAnimal(FakeResource[Animal]):
    id: str | None = None
    name: str | None = None
    item_type: type[Animal] = field(default=Animal)

    @cached_property
    def _raw(self) -> dict[str, Any]:
        return {
            "id": self.id or self.fake.uuid(),
            "name": self.name or self.fake.text(length=10),
            "age": self.fake.number(),
            "idempotency_id": None,
        }


@pytest.fixture
def repository() -> Repository[Animal]:
    return InMemoryRepository[Animal](InMemoryByteStore())


@pytest.fixture
def service(repository: Repository[Animal]) -> RestfulServiceShell[Animal]:
    return RestfulServiceShell(
        inner=RestfulRepository(repository),
        formatter=DataclassFormatter(Animal),
    )


def test_should_create_one(
    repository: Repository[Animal],
    service: RestfulServiceShell[Animal],
) -> None:
    # Given
    animal = FakeAnimal()

    # When
    result = service.create_one(animal.json())

    # Then
    assert result == animal.json()
    assert repository.read(animal.entity().id) == animal.entity()


def test_should_not_create_one(
    repository: Repository[Animal],
    service: RestfulServiceShell[Animal],
) -> None:
    # Given
    animal = FakeAnimal()
    repository.create(animal.entity())

    # Then
    with pytest.raises(ExistsError):
        # When
        service.create_one(animal.json())


def test_should_read_one(
    repository: Repository[Animal],
    service: RestfulServiceShell[Animal],
) -> None:
    # Given
    animal = FakeAnimal()
    repository.create(animal.entity())

    # When
    result = service.read_one(animal.entity().id)

    # Then
    assert result == animal.json()


def test_should_not_read_unknown(
    service: RestfulServiceShell[Animal],
) -> None:
    # Given
    animal = FakeAnimal()

    # Then
    with pytest.raises(DoesNotExistError):
        # When
        service.read_one(animal.entity().id)


def test_should_read_all(
    repository: Repository[Animal],
    service: RestfulServiceShell[Animal],
) -> None:
    # Given
    animal_1 = FakeAnimal()
    animal_2 = FakeAnimal()
    repository.create(animal_1.entity())
    repository.create(animal_2.entity())

    # When
    result = service.read_all()

    # Then
    assert result == [animal_1.json(), animal_2.json()]


def test_should_update_one(
    repository: Repository[Animal],
    service: RestfulServiceShell[Animal],
) -> None:
    # Given
    initial = FakeAnimal().entity()
    updated = FakeAnimal(id=initial.id, name=initial.name)
    repository.create(initial)

    # When
    result = service.update_one(updated.entity().id, age=updated.entity().age)

    # Then
    assert result == updated.json()
    assert repository.read(updated.entity().id) == updated.entity()


def test_should_not_update_unknown(
    service: RestfulServiceShell[Animal],
) -> None:
    # Given
    updated = FakeAnimal()

    # Then
    with pytest.raises(DoesNotExistError):
        # When
        service.update_one(updated.entity().id, age=updated.entity().age)


def test_should_replace_one(
    repository: Repository[Animal],
    service: RestfulServiceShell[Animal],
) -> None:
    # Given
    initial = FakeAnimal().entity()
    replaced = FakeAnimal(id=initial.id)
    repository.create(initial)

    # When
    result = service.replace_one(replaced.json())

    # Then
    assert result == replaced.json()
    assert repository.read(replaced.entity().id) == replaced.entity()


def test_should_not_replace_unknown(
    service: RestfulServiceShell[Animal],
) -> None:
    # Given
    replaced = FakeAnimal()

    # Then
    with pytest.raises(DoesNotExistError):
        # When
        service.replace_one(replaced.json())


def test_should_delete_one(
    repository: Repository[Animal],
    service: RestfulServiceShell[Animal],
) -> None:
    # Given
    animal = FakeAnimal()
    repository.create(animal.entity())

    # When
    service.delete_one(animal.entity().id)

    # Then
    assert len(repository) == 0


def test_should_not_delete_unknown(
    service: RestfulServiceShell[Animal],
) -> None:
    # Given
    animal = FakeAnimal()

    # Then
    with pytest.raises(DoesNotExistError):
        # When
        service.delete_one(animal.entity().id)

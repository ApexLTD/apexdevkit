from typing import Any

import pytest
from _pytest.fixtures import fixture
from faker.generator import random

from apexdevkit.error import DoesNotExistError, ExistsError
from apexdevkit.repository.alternative import MemoryRepositoryBase
from apexdevkit.testing.fake import Fake


@fixture
def repository() -> MemoryRepositoryBase:
    return MemoryRepositoryBase()


def fake_person() -> dict[str, Any]:
    return {
        "id": Fake().uuid(),
        "name": Fake().last_name(),
    }


def test_should_create(repository: MemoryRepositoryBase) -> None:
    fake = fake_person()
    repository.create(fake)

    assert repository.items[fake["id"]] == fake


def test_should_create_many(repository: MemoryRepositoryBase) -> None:
    fakes = [fake_person() for _ in range(10)]
    repository.create_many(fakes)

    for fake in fakes:
        assert repository.items[fake["id"]] == fake


def test_should_read(repository: MemoryRepositoryBase) -> None:
    fake = fake_person()
    repository.create(fake)

    assert repository.read(fake["id"]) == fake


def test_should_read_many(repository: MemoryRepositoryBase) -> None:
    fakes = [fake_person() for _ in range(10)]
    repository.create_many(fakes)

    assert fakes == list(repository)


def test_should_update(repository: MemoryRepositoryBase) -> None:
    fake = fake_person()
    repository.create(fake)

    fake["name"] = "updated"

    repository.update(fake)

    assert fake == repository.read(fake["id"])


def test_should_update_many(repository: MemoryRepositoryBase) -> None:
    fakes = [fake_person() for _ in range(10)]
    repository.create_many(fakes)

    for i, fake in enumerate(fakes):
        fake["name"] = f"updated_{i}"

    repository.update_many(fakes)

    assert fakes == list(repository)


def test_should_delete(repository: MemoryRepositoryBase) -> None:
    fake = fake_person()
    repository.create(fake)

    repository.delete(fake["id"])

    with pytest.raises(DoesNotExistError):
        repository.read(fake["id"])


def test_correct_length(repository: MemoryRepositoryBase) -> None:
    random_length = random.randint(1, 10)
    fakes = [fake_person() for _ in range(random_length)]

    repository.create_many(fakes)

    assert random_length == len(repository)


def test_should_not_create_duplicate(repository: MemoryRepositoryBase) -> None:
    fake = fake_person()

    repository.create(fake)

    with pytest.raises(ExistsError):
        repository.create(fake)


def test_should_not_create_many_duplicates(repository: MemoryRepositoryBase) -> None:
    fakes = [fake_person() for _ in range(10)]

    repository.create_many(fakes)

    with pytest.raises(ExistsError):
        repository.create_many(fakes)


def test_should_not_update_nonexistent(repository: MemoryRepositoryBase) -> None:
    fake = fake_person()

    with pytest.raises(DoesNotExistError):
        repository.update(fake)


def test_should_not_update_many_nonexistent(repository: MemoryRepositoryBase) -> None:
    fakes = [fake_person() for _ in range(10)]

    with pytest.raises(DoesNotExistError):
        repository.update_many(fakes)


def test_should_not_delete_nonexistent(repository: MemoryRepositoryBase) -> None:
    fake = fake_person()

    with pytest.raises(DoesNotExistError):
        repository.delete(fake["id"])

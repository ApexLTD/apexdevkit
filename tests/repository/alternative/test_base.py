from typing import Any

import pytest
from _pytest.fixtures import fixture
from faker.generator import random

from apexdevkit.error import DoesNotExistError
from apexdevkit.repository.alternative import NewRepositoryBase
from apexdevkit.testing.fake import Fake


@fixture
def repository() -> NewRepositoryBase:
    return NewRepositoryBase()


def fake_crypto() -> dict[str, Any]:
    return {
        "id": Fake().uuid(),
        "name": Fake().last_name(),
    }


def test_should_create(repository: NewRepositoryBase) -> None:
    fake = fake_crypto()
    repository.create(fake)

    assert repository.items[fake["id"]] == fake


def test_should_create_many(repository: NewRepositoryBase) -> None:
    fakes = [fake_crypto() for _ in range(10)]
    repository.create_many(fakes)

    for fake in fakes:
        assert repository.items[fake["id"]] == fake


def test_should_read(repository: NewRepositoryBase) -> None:
    fake = fake_crypto()
    repository.create(fake)

    assert repository.read(fake["id"]) == fake


def test_should_read_many(repository: NewRepositoryBase) -> None:
    fakes = [fake_crypto() for _ in range(10)]
    repository.create_many(fakes)

    assert fakes == list(repository)


def test_should_update(repository: NewRepositoryBase) -> None:
    fake = fake_crypto()
    repository.create(fake)

    fake["name"] = "updated"

    repository.update(fake)

    assert fake == repository.read(fake["id"])


def test_should_update_many(repository: NewRepositoryBase) -> None:
    fakes = [fake_crypto() for _ in range(10)]
    repository.create_many(fakes)

    for i, fake in enumerate(fakes):
        fake["name"] = f"updated_{i}"

    repository.update_many(fakes)

    assert fakes == list(repository)


def test_should_delete(repository: NewRepositoryBase) -> None:
    fake = fake_crypto()
    repository.create(fake)

    repository.delete(fake["id"])

    with pytest.raises(DoesNotExistError):
        repository.read(fake["id"])


def test_correct_length(repository: NewRepositoryBase) -> None:
    random_length = random.randint(1, 10)
    fakes = [fake_crypto() for _ in range(random_length)]

    repository.create_many(fakes)

    assert random_length == len(repository)

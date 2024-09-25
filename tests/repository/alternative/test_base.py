from typing import Any

from _pytest.fixtures import fixture

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

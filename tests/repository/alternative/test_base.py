from typing import Any

from _pytest.fixtures import fixture

from apexdevkit.repository.alternative import NewRepositoryBase


@fixture
def repository() -> NewRepositoryBase:
    return NewRepositoryBase()


def fake() -> dict[str, Any]:
    return {
        "id": "id",
        "name": "apple",
    }


def test_should_create(repository: NewRepositoryBase) -> None:
    repository.create(fake())

    assert repository.items[fake()["id"]] == fake()

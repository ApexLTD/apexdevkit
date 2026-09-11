from uuid import uuid4

import pytest
from pypebbles import JsonDict

from apexdevkit.error import ForbiddenError
from tests.fastapi.rest import RestCollection
from tests.fastapi.sample_api import FailingService, FakeApple


@pytest.fixture
def apple() -> JsonDict:
    return FakeApple().json()


@pytest.fixture
def service() -> FailingService:
    return FailingService(ForbiddenError)


def test_should_not_create_forbidden(apple: JsonDict, resource: RestCollection) -> None:
    (
        resource.create_one()
        .from_data(apple)
        .ensure()
        .fail()
        .with_code(403)
        .and_message("Forbidden")
    )


def test_should_not_read_forbidden(resource: RestCollection) -> None:
    (
        resource.item(with_id=uuid4())
        .read()
        .ensure()
        .fail()
        .with_code(403)
        .and_message("Forbidden")
    )


def test_should_not_read_many_forbidden(read_many_resource: RestCollection) -> None:
    (
        read_many_resource.read(color="red")
        .ensure()
        .fail()
        .with_code(403)
        .and_message("Forbidden")
    )


def test_should_not_read_all_forbidden(resource: RestCollection) -> None:
    resource.read().ensure().fail().with_code(403).and_message("Forbidden")


def test_should_not_update_forbidden(apple: JsonDict, resource: RestCollection) -> None:
    (
        resource.item(with_id=apple["id"])
        .update_one()
        .and_data(apple)
        .ensure()
        .fail()
        .with_code(403)
        .and_message("Forbidden")
    )


def test_should_not_replace_forbidden(
    apple: JsonDict, resource: RestCollection
) -> None:
    (
        resource.replace_one()
        .from_data(apple)
        .ensure()
        .fail()
        .with_code(403)
        .and_message("Forbidden")
    )


def test_should_not_delete_forbidden(apple: JsonDict, resource: RestCollection) -> None:
    (
        resource.item(with_id=apple["id"])
        .delete_one()
        .ensure()
        .fail()
        .with_code(403)
        .and_message("Forbidden")
    )

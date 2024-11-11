from uuid import uuid4

import pytest

from apexdevkit.error import ForbiddenError
from apexdevkit.http import JsonDict
from apexdevkit.testing.rest import RestCollection
from tests.resource.sample_api import FailingService
from tests.resource.setup import FakeApple


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


def test_should_not_create_many_forbidden(
    apple: JsonDict, resource: RestCollection
) -> None:
    (
        resource.create_many()
        .from_collection([apple])
        .ensure()
        .fail()
        .with_code(403)
        .and_message("Forbidden")
    )


def test_should_not_read_forbidden(resource: RestCollection) -> None:
    (
        resource.read_one()
        .with_id(uuid4())
        .ensure()
        .fail()
        .with_code(403)
        .and_message("Forbidden")
    )


@pytest.mark.skip
def test_should_not_read_many_forbidden(read_many_resource: RestCollection) -> None:
    read_many_resource.read_many(params={"color": 0}).ensure().fail().with_code(403).and_message("Forbidden")


def test_should_not_read_all_forbidden(resource: RestCollection) -> None:
    resource.read_all().ensure().fail().with_code(403).and_message("Forbidden")


def test_should_not_update_forbidden(apple: JsonDict, resource: RestCollection) -> None:
    (
        resource.update_one()
        .with_id(apple["id"])
        .and_data(apple)
        .ensure()
        .fail()
        .with_code(403)
        .and_message("Forbidden")
    )


def test_should_not_update_many_forbidden(
    apple: JsonDict, resource: RestCollection
) -> None:
    (
        resource.update_many()
        .from_collection([apple])
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


def test_should_not_replace_many_forbidden(
    apple: JsonDict, resource: RestCollection
) -> None:
    (
        resource.replace_many()
        .from_collection([apple])
        .ensure()
        .fail()
        .with_code(403)
        .and_message("Forbidden")
    )


def test_should_not_delete_forbidden(apple: JsonDict, resource: RestCollection) -> None:
    (
        resource.delete_one()
        .with_id(apple["id"])
        .ensure()
        .fail()
        .with_code(403)
        .and_message("Forbidden")
    )

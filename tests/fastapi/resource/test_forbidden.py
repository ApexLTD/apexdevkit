from uuid import uuid4

import pytest

from apexdevkit.error import ForbiddenError
from apexdevkit.http import JsonDict
from apexdevkit.testing.rest import RestCollection
from tests.fastapi.resource.sample_api import FailingService
from tests.fastapi.resource.setup import FakeApple


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


def test_should_not_filter_forbidden(resource: RestCollection) -> None:
    (
        resource.filter_with()
        .from_data(
            JsonDict()
            .with_a(filter=None)
            .and_a(condition=None)
            .and_a(ordering=[])
            .and_a(
                paging=JsonDict()
                .with_a(page=None)
                .and_a(length=None)
                .and_a(offset=None)
            )
        )
        .ensure()
        .fail()
        .with_code(403)
        .and_message("Forbidden")
    )


def test_should_not_read_many_forbidden(read_many_resource: RestCollection) -> None:
    read_many_resource.read_many(color="red").ensure().fail().with_code(
        403
    ).and_message("Forbidden")


def test_should_not_read_aggregated_forbidden(
    resource: RestCollection,
) -> None:
    (
        resource.aggregate_with()
        .from_data(
            JsonDict()
            .with_a(filter=None)
            .and_a(condition=None)
            .and_a(
                aggregations=[JsonDict().with_a(name=None).and_a(aggregation="COUNT")]
            )
        )
        .ensure()
        .fail()
        .with_code(403)
        .and_message("Forbidden")
    )


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

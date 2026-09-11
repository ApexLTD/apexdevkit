from __future__ import annotations

from uuid import uuid4

import pytest
from pypebbles import JsonDict

from apexdevkit.fastapi.name import RestfulName
from tests.fastapi.rest import RestCollection
from tests.fastapi.sample_api import FakeApple, SuccessfulService


@pytest.fixture
def apple() -> JsonDict:
    return FakeApple().json()


@pytest.fixture
def service(apple: JsonDict) -> SuccessfulService:
    return SuccessfulService(always_return=apple)


def test_should_create(
    apple: JsonDict,
    service: SuccessfulService,
    resource: RestCollection,
) -> None:
    (
        resource.create()
        .from_data(apple)
        .ensure()
        .success()
        .with_code(201)
        .and_item(apple)
    )

    assert service.called_with == apple.drop("id")


def test_should_read_one(
    apple: JsonDict,
    service: SuccessfulService,
    resource: RestCollection,
) -> None:
    (
        resource.item(with_id=apple["id"])
        .read()
        .ensure()
        .success()
        .with_code(200)
        .with_item(apple)
    )

    assert service.called_with == apple["id"]


def test_should_read_many(
    apple: JsonDict,
    service: SuccessfulService,
    read_many_resource: RestCollection,
) -> None:
    (
        read_many_resource.read(color="red")
        .ensure()
        .success()
        .with_code(200)
        .with_collection([apple])
    )

    assert service.called_with == {"color": "red"}


def test_should_read_all(
    apple: JsonDict,
    service: SuccessfulService,
    resource: RestCollection,
) -> None:
    resource.read().ensure().success().with_code(200).and_collection([apple])

    assert service.called_with is None


def test_should_update_one(
    apple: JsonDict,
    service: SuccessfulService,
    resource: RestCollection,
) -> None:
    (
        resource.item(with_id=apple["id"])
        .update()
        .and_data(apple)
        .ensure()
        .success()
        .with_code(200)
    )

    assert service.called_with == (apple["id"], apple.drop("id").drop("color"))


def test_should_replace_one(
    apple: JsonDict,
    service: SuccessfulService,
    resource: RestCollection,
) -> None:
    resource.replace().from_data(apple).ensure().success().with_code(200)

    assert service.called_with == apple


def test_should_delete_one(
    apple: JsonDict,
    service: SuccessfulService,
    resource: RestCollection,
) -> None:
    resource.item(with_id=apple["id"]).delete().ensure().success().with_code(200)

    assert service.called_with == apple["id"]


def test_should_sub_resource(resource: RestCollection) -> None:
    (
        resource.item(with_id=str(uuid4()))
        .sub_resource(name=RestfulName("price"))
        .delete()
        .ensure()
        .success()
        .with_code(200)
    )

from __future__ import annotations

from uuid import uuid4

import pytest

from apexdevkit.fastapi.query import (
    Aggregation,
    AggregationOption,
    FooterOptions,
    Page,
    QueryOptions,
)
from apexdevkit.http import JsonDict
from apexdevkit.testing import RestCollection
from tests.resource.sample_api import SuccessfulService
from tests.resource.setup import FakeApple


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
        resource.create_one()
        .from_data(apple)
        .ensure()
        .success()
        .with_code(201)
        .and_item(apple)
    )

    assert service.called_with == apple.drop("id")


def test_should_create_many(
    apple: JsonDict,
    service: SuccessfulService,
    resource: RestCollection,
) -> None:
    (
        resource.create_many()
        .from_collection([apple])
        .ensure()
        .success()
        .with_code(201)
        .and_collection([apple])
    )

    assert service.called_with == [apple.drop("id")]


def test_should_read_one(
    apple: JsonDict,
    service: SuccessfulService,
    resource: RestCollection,
) -> None:
    (
        resource.read_one()
        .with_id(apple["id"])
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
        read_many_resource.read_many(color="red")
        .ensure()
        .success()
        .with_code(200)
        .with_collection([apple])
    )

    assert service.called_with == {"color": "red"}


def test_should_read_filtered(
    apple: JsonDict,
    service: SuccessfulService,
    resource: RestCollection,
) -> None:
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
        .success()
        .with_code(200)
        .with_collection([apple])
    )

    assert service.called_with == QueryOptions(None, None, [], Page(None, None, None))


def test_should_read_all(
    apple: JsonDict,
    service: SuccessfulService,
    resource: RestCollection,
) -> None:
    resource.read_all().ensure().success().with_code(200).and_collection([apple])

    assert service.called_with is None


def test_should_read_aggregated(
    apple: JsonDict,
    service: SuccessfulService,
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
        .success()
        .with_code(200)
        .with_collection([])
    )

    assert service.called_with == FooterOptions(
        None, None, [AggregationOption(None, Aggregation.COUNT)]
    )


def test_should_update_one(
    apple: JsonDict,
    service: SuccessfulService,
    resource: RestCollection,
) -> None:
    (
        resource.update_one()
        .with_id(apple["id"])
        .and_data(apple)
        .ensure()
        .success()
        .with_code(200)
    )

    assert service.called_with == (apple["id"], apple.drop("id").drop("color"))


def test_should_update_many(
    apple: JsonDict,
    service: SuccessfulService,
    resource: RestCollection,
) -> None:
    resource.update_many().from_collection([apple]).ensure().success().with_code(200)

    assert service.called_with == [apple.drop("color")]


def test_should_replace_one(
    apple: JsonDict,
    service: SuccessfulService,
    resource: RestCollection,
) -> None:
    resource.replace_one().from_data(apple).ensure().success().with_code(200)

    assert service.called_with == apple


def test_should_replace_many(
    apple: JsonDict,
    service: SuccessfulService,
    resource: RestCollection,
) -> None:
    resource.replace_many().from_collection([apple]).ensure().success().with_code(200)

    assert service.called_with == [apple]


def test_should_delete_one(
    apple: JsonDict,
    service: SuccessfulService,
    resource: RestCollection,
) -> None:
    resource.delete_one().with_id(apple["id"]).ensure().success().with_code(200)

    assert service.called_with == apple["id"]


def test_should_sub_resource(apple: JsonDict, resource: RestCollection) -> None:
    (
        resource.sub_resource(str(uuid4()))
        .sub_resource("price")
        .delete_one()
        .with_id(str(uuid4()))
        .ensure()
        .success()
        .with_code(200)
    )

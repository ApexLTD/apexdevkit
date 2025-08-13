from __future__ import annotations

from uuid import uuid4

import pytest

from apexdevkit.formatter import DataclassFormatter
from apexdevkit.http import JsonDict
from apexdevkit.query.query import (
    Aggregation,
    AggregationOption,
    DateValue,
    Filter,
    FooterOptions,
    Leaf,
    Operation,
    Operator,
    Page,
    QueryOptions,
    Sort,
)
from apexdevkit.testing import RestCollection
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
            .with_a(filter=JsonDict().with_a(args=[JsonDict().with_a(date="20221212")]))
            .and_a(
                condition=JsonDict()
                .with_a(operation="NOT")
                .and_a(operands=[JsonDict().with_a(name="test").and_a(values=[])])
            )
            .and_a(ordering=[JsonDict().with_a(name="test").and_a(is_descending=False)])
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

    assert service.called_with == DataclassFormatter(QueryOptions).dump(
        QueryOptions(
            Filter(args=[DateValue("20221212")]),
            Operator(Operation.NOT, [Leaf("test", [])]),
            [Sort("test", False)],
            Page(None, None, None),
        )
    )


def test_should_read_summed(
    service: SuccessfulService,
    resource: RestCollection,
) -> None:
    (
        resource.aggregation_with()
        .from_data(JsonDict().with_a(is_rotten=True))
        .ensure()
        .success()
        .with_code(200)
    )

    assert service.called_with == {"is_rotten": True}


def test_should_read_all(
    apple: JsonDict,
    service: SuccessfulService,
    resource: RestCollection,
) -> None:
    resource.read_all().ensure().success().with_code(200).and_collection([apple])

    assert service.called_with is None


def test_should_read_aggregated(
    service: SuccessfulService,
    resource: RestCollection,
) -> None:
    (
        resource.aggregate_with()
        .from_data(
            JsonDict()
            .with_a(filter=JsonDict().with_a(args=[JsonDict().with_a(date="20221212")]))
            .and_a(
                condition=JsonDict()
                .with_a(operation="NOT")
                .and_a(operands=[JsonDict().with_a(name="test").and_a(values=[])])
            )
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
        Filter(args=[DateValue("20221212")]),
        Operator(Operation.NOT, [Leaf("test", [])]),
        [AggregationOption(None, Aggregation.COUNT)],
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


def test_should_sub_resource(resource: RestCollection) -> None:
    (
        resource.sub_resource(str(uuid4()))
        .sub_resource("price")
        .delete_one()
        .with_id(str(uuid4()))
        .ensure()
        .success()
        .with_code(200)
    )

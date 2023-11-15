from __future__ import annotations

from dataclasses import dataclass, field
from unittest.mock import ANY
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from pydantic import BaseModel
from starlette.testclient import TestClient

from pydevtools.error import DoesNotExistError, ExistsError
from pydevtools.fastapi import (
    BadRequest,
    NoData,
    ResourceCreated,
    ResourceExists,
    ResourceFound,
    ResourceNotFound,
    Response,
)
from pydevtools.http import Httpx
from pydevtools.repository import InMemoryRepository
from pydevtools.testing import RestfulName, RestResource


@dataclass
class Apple:
    color: str
    name: str

    id: UUID = field(default_factory=uuid4)

    def __eq__(self, other: object) -> bool:
        assert isinstance(other, Apple), f"Cannot compare to {type(other)}"

        return self.name == other.name


app = FastAPI()
apples = InMemoryRepository[Apple]()


class AppleItem(BaseModel):
    id: UUID
    name: str
    color: str


class AppleItemEnvelope(BaseModel):
    apple: AppleItem


class AppleListEnvelope(BaseModel):
    count: int
    apples: list[AppleItem]


class AppleCreateRequest(BaseModel):
    name: str
    color: str


@app.post(
    "/apples",
    status_code=201,
    response_model=Response[AppleItemEnvelope],
)
def create(request: AppleCreateRequest) -> ResourceCreated | ResourceExists:
    apple = Apple(**request.model_dump())

    try:
        apples.create(apple)
    except ExistsError as e:
        return ResourceExists(
            f"An apple with the name<{apple.name}> already exists.",
            apple={"id": str(e.id)},
        )

    return ResourceCreated(apple=apple)


@app.get(
    "/apples/{apple_id}",
    status_code=200,
    response_model=Response[AppleItemEnvelope],
)
def read_one(apple_id: UUID) -> ResourceFound | ResourceNotFound:
    try:
        return ResourceFound(apple=apples.read(apple_id))
    except DoesNotExistError:
        return ResourceNotFound(message=f"An apple with id<{apple_id}> does not exist.")


@app.get(
    "/apples",
    status_code=200,
    response_model=Response[AppleListEnvelope],
)
def read_all() -> ResourceFound:
    return ResourceFound(apples=list(apples), count=len(apples))


@app.patch("/apples/{apple_id}", response_model=Response[NoData])
def patch(apple_id: UUID) -> BadRequest:
    return BadRequest(message=f"Patching <{apple_id}> is not allowed")


@pytest.fixture
def http() -> TestClient:
    apples.items = {}

    return TestClient(app)


@pytest.fixture
def resource(http: Httpx) -> RestResource:
    return RestResource(http, RestfulName("apple"))


def test_should_not_read_unknown(resource: RestResource) -> None:
    unknown_id = uuid4()

    (
        resource.read_one()
        .with_id(unknown_id)
        .ensure()
        .fail()
        .with_code(404)
        .and_message(f"An apple with id<{unknown_id}> does not exist.")
    )


def test_should_create(resource: RestResource) -> None:
    apple = {"name": "Golden", "color": "Golden"}

    (
        resource.create_one()
        .from_data(apple)
        .ensure()
        .success()
        .with_code(201)
        .and_data(apple={"id": ANY, **apple})
    )


def test_should_persist(resource: RestResource) -> None:
    apple = {"name": "Golden", "color": "Golden"}
    id_ = resource.create_one().from_data(apple).unpack().value_of("id").to(str)

    (
        resource.read_one()
        .with_id(id_)
        .ensure()
        .success()
        .with_code(200)
        .and_data(apple={"id": id_, **apple})
    )


def test_should_not_duplicate(resource: RestResource) -> None:
    apple = {"name": "Golden", "color": "Golden"}
    id_ = resource.create_one().from_data(apple).unpack().value_of("id").to(str)

    (
        resource.create_one()
        .from_data(apple)
        .ensure()
        .fail()
        .with_code(409)
        .and_message(f"An apple with the name<{apple['name']}> already exists.")
        .and_data(apple={"id": id_})
    )


def test_should_not_list_anything_when_none_exist(resource: RestResource) -> None:
    resource.read_all().ensure().success().with_code(200).and_data(apples=[], count=0)


def test_should_list_all_created(resource: RestResource) -> None:
    apple_1 = {"name": "Golden", "color": "Golden"}
    apple_2 = {"name": "Ambrosia", "color": "Red"}
    partners = [
        dict(resource.create_one().from_data(apple_1).unpack()),
        dict(resource.create_one().from_data(apple_2).unpack()),
    ]

    (
        resource.read_all()
        .ensure()
        .success()
        .with_code(200)
        .and_data(apples=partners, count=2)
    )


def test_should_not_patch(resource: RestResource) -> None:
    id_ = uuid4()
    (
        resource.update_one()
        .with_id(id_)
        .and_data({"color": "Green"})
        .ensure()
        .fail()
        .with_code(400)
        .and_message(f"Patching <{id_}> is not allowed")
    )

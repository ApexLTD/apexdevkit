from __future__ import annotations

from dataclasses import dataclass, field
from unittest.mock import ANY
from uuid import UUID, uuid4

import pytest
from faker import Faker
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
from pydevtools.http import Httpx, JsonObject
from pydevtools.repository import InMemoryRepository
from pydevtools.testing import RestfulName, RestResource


@dataclass
class Apple:
    color: str
    name: str

    id: UUID = field(default_factory=uuid4)


app = FastAPI()
apples = InMemoryRepository[Apple]().with_unique("name")


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


class AppleCreateManyRequest(BaseModel):
    apples: list[AppleCreateRequest]


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
            f"An apple with the {e} already exists.",
            apple={"id": str(e.id)},
        )

    return ResourceCreated(apple=apple)


@app.post(
    "/apples/batch",
    status_code=201,
    response_model=Response[AppleListEnvelope],
)
def create_many(requests: AppleCreateManyRequest) -> ResourceCreated | ResourceExists:
    result = [Apple(**request.model_dump()) for request in requests.apples]

    try:
        apples.create_many(result)
    except ExistsError as e:
        return ResourceExists(
            f"An apple with the {e} already exists.",
            apple={"id": str(e.id)},
        )

    return ResourceCreated(apples=result, count=len(result))


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


@dataclass
class Fake:
    faker: Faker = field(default_factory=Faker)

    def apple(self) -> JsonObject[str]:
        return JsonObject(
            {
                "name": self.faker.name(),
                "color": self.faker.color(),
            }
        )


fake = Fake()


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


def test_should_not_list_anything_when_none_exist(resource: RestResource) -> None:
    resource.read_all().ensure().success().with_code(200).and_data()


def test_should_create(resource: RestResource) -> None:
    apple = fake.apple()

    (
        resource.create_one()
        .from_data(apple)
        .ensure()
        .success()
        .with_code(201)
        .and_data(apple.with_a(id=ANY))
    )


def test_should_persist(resource: RestResource) -> None:
    apple = resource.create_one().from_data(fake.apple()).unpack()

    (
        resource.read_one()
        .with_id(apple.value_of("id").to(str))
        .ensure()
        .success()
        .with_code(200)
        .and_data(apple)
    )


def test_should_not_duplicate(resource: RestResource) -> None:
    apple = resource.create_one().from_data(fake.apple()).unpack()

    (
        resource.create_one()
        .from_data(apple.drop("id"))
        .ensure()
        .fail()
        .with_code(409)
        .and_message(
            f"An apple with the name<{apple.value_of('name').to(str)}> already exists."
        )
        .and_data(apple.select("id"))
    )


def test_should_not_patch(resource: RestResource) -> None:
    id_ = uuid4()

    (
        resource.update_one()
        .with_id(id_)
        .and_data(fake.apple().drop("name"))
        .ensure()
        .fail()
        .with_code(400)
        .and_message(f"Patching <{id_}> is not allowed")
    )


def test_should_create_many(resource: RestResource) -> None:
    many_apples = [fake.apple(), fake.apple()]

    (
        resource.create_many()
        .from_data(many_apples[0])
        .and_data(many_apples[1])
        .ensure()
        .success()
        .with_code(201)
        .and_data(many_apples[0].with_a(id=ANY), many_apples[1].with_a(id=ANY))
    )


def test_should_persist_many(resource: RestResource) -> None:
    many_apples = (
        resource.create_many()
        .from_data(fake.apple())
        .and_data(fake.apple())
        .unpack_many()
    )

    resource.read_all().ensure().success().with_code(200).and_data(*many_apples)


def test_should_not_duplicate_many(resource: RestResource) -> None:
    apple = resource.create_one().from_data(fake.apple()).unpack()

    (
        resource.create_many()
        .from_data(apple.drop("id"))
        .and_data(apple.drop("id"))
        .ensure()
        .fail()
        .with_code(409)
        .and_message(
            f"An apple with the name<{apple.value_of('name').to(str)}> already exists."
        )
        .and_data(apple.select("id"))
    )

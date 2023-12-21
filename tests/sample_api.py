from __future__ import annotations

from dataclasses import dataclass, field
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter
from pydantic import BaseModel

from pydevtools.error import DoesNotExistError, ExistsError
from pydevtools.fastapi import (
    BadRequest,
    NoData,
    ResourceCreated,
    ResourceExists,
    ResourceFound,
    ResourceNotFound,
    Response,
    inject,
)
from pydevtools.repository import InMemoryRepository

apple_api = APIRouter()


@dataclass
class Apple:
    color: str
    name: str

    id: UUID = field(default_factory=uuid4)


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


@apple_api.post(
    "",
    status_code=201,
    response_model=Response[AppleItemEnvelope],
)
def create(
    request: AppleCreateRequest,
    apples: Annotated[InMemoryRepository[Apple], inject("apples")],
) -> ResourceCreated | ResourceExists:
    apple = Apple(**request.model_dump())

    try:
        apples.create(apple)
    except ExistsError as e:
        return ResourceExists(
            f"An apple with the {e} already exists.",
            apple={"id": str(e.id)},
        )

    return ResourceCreated(apple=apple)


@apple_api.post(
    "/batch",
    status_code=201,
    response_model=Response[AppleListEnvelope],
)
def create_many(
    requests: AppleCreateManyRequest,
    apples: Annotated[InMemoryRepository[Apple], inject("apples")],
) -> ResourceCreated | ResourceExists:
    result = [Apple(**request.model_dump()) for request in requests.apples]

    try:
        apples.create_many(result)
    except ExistsError as e:
        return ResourceExists(
            f"An apple with the {e} already exists.",
            apple={"id": str(e.id)},
        )

    return ResourceCreated(apples=result, count=len(result))


@apple_api.get(
    "/{apple_id}",
    status_code=200,
    response_model=Response[AppleItemEnvelope],
)
def read_one(
    apple_id: UUID,
    apples: Annotated[InMemoryRepository[Apple], inject("apples")],
) -> ResourceFound | ResourceNotFound:
    try:
        return ResourceFound(apple=apples.read(apple_id))
    except DoesNotExistError:
        return ResourceNotFound(message=f"An apple with id<{apple_id}> does not exist.")


@apple_api.get(
    "",
    status_code=200,
    response_model=Response[AppleListEnvelope],
)
def read_all(
    apples: Annotated[InMemoryRepository[Apple], inject("apples")]
) -> ResourceFound:
    return ResourceFound(apples=list(apples), count=len(apples))


@apple_api.patch("/{apple_id}", response_model=Response[NoData])
def patch(apple_id: UUID) -> BadRequest:
    return BadRequest(message=f"Patching <{apple_id}> is not allowed")

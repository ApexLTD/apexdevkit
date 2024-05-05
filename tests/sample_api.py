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
    SuccessResponse,
    inject,
)
from pydevtools.repository import InMemoryRepository

apple_api = APIRouter()


@dataclass(frozen=True)
class Apple:
    color: str
    name: str

    id: UUID = field(default_factory=uuid4)


class AppleItem(BaseModel):
    id: UUID
    name: str
    color: str

    def apple(self) -> Apple:
        return Apple(id=self.id, name=self.name, color=self.color)


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


class AppleUpdateListEnvelope(BaseModel):
    apples: list[AppleItem]


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
    apples: Annotated[InMemoryRepository[Apple], inject("apples")],
    color: str | None = None,
) -> ResourceFound:
    filtered_apples = (
        [apple for apple in apples if apple.color == color] if color else list(apples)
    )

    return ResourceFound(apples=filtered_apples, count=len(apples))


@apple_api.patch(
    "/{apple_id}",
    status_code=200,
    response_model=Response[NoData],
)
def patch(apple_id: UUID) -> BadRequest:
    return BadRequest(message=f"Patching <{apple_id}> is not allowed")


@apple_api.patch("", status_code=200, response_model=Response[NoData])
def patch_many(
    updated: AppleUpdateListEnvelope,
    apples: Annotated[InMemoryRepository[Apple], inject("apples")],
) -> SuccessResponse:
    apples.update_many([apple.apple() for apple in updated.apples])
    return SuccessResponse(status_code=200)


@apple_api.delete(
    "/{apple_id}",
    status_code=200,
    response_model=Response[NoData],
)
def delete(
    apple_id: UUID, apples: Annotated[InMemoryRepository[Apple], inject("apples")]
) -> ResourceNotFound | ResourceFound:
    try:
        apples.delete(apple_id)
    except DoesNotExistError:
        return ResourceNotFound(message=f"An apple with id<{apple_id}> does not exist.")

    return ResourceFound()

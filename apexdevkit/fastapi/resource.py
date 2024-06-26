from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, Callable, Self

from starlette.responses import JSONResponse

from apexdevkit.error import DoesNotExistError, ExistsError, ForbiddenError
from apexdevkit.fastapi.builder import RestfulServiceBuilder
from apexdevkit.fastapi.response import RestfulResponse
from apexdevkit.testing import RestfulName

_Response = JSONResponse | dict[str, Any]


@dataclass
class ApiResource:
    name: RestfulName = field(init=False)
    infra: RestfulServiceBuilder = field(init=False)

    parent: str = field(init=False, default="")

    @cached_property
    def response(self) -> RestfulResponse:
        return RestfulResponse(name=self.name)

    def with_name(self, name: RestfulName) -> Self:
        self.name = name

        return self

    def with_infra(self, infra: RestfulServiceBuilder) -> Self:
        self.infra = infra

        return self

    def with_parent(self, parent: str) -> Self:
        self.parent = parent

        return self

    def create_one(self, User, ParentId, Item) -> Callable[..., _Response]:  # type: ignore
        def endpoint(user: User, parent_id: ParentId, item: Item) -> _Response:
            try:
                service = self.infra.with_user(user).with_parent(parent_id).build()
            except DoesNotExistError as e:
                return JSONResponse(
                    RestfulResponse(RestfulName(self.parent)).not_found(e), 404
                )

            try:
                item = service.create_one(item)
            except ExistsError as e:
                return JSONResponse(self.response.exists(e), 409)
            except ForbiddenError as e:
                return JSONResponse(self.response.forbidden(e), 403)

            return self.response.created_one(item)

        return endpoint

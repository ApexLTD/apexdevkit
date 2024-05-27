from dataclasses import dataclass, field
from typing import Annotated, Any, Iterable, Self, TypeVar

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from apexdevkit.error import DoesNotExistError, ExistsError
from apexdevkit.fastapi.schema import RestfulSchema
from apexdevkit.fastapi.service import RawCollection, RawItem, RestfulService
from apexdevkit.testing import RestfulName

_Response = JSONResponse | dict[str, Any]


@dataclass
class RestfulResponse:
    name: RestfulName

    @classmethod
    def from_dataclass(cls, value: type[Any]) -> "RestfulResponse":
        return cls(name=RestfulName(value.__name__.lower()))

    def _response(self, code: int, data: Any, error: str = "") -> dict[str, Any]:
        content: dict[str, Any] = {"code": code, "status": "success"}

        if error:
            content["status"] = "fail"
            content["error"] = {"message": error}

        match data:
            case None:
                content["data"] = {}
            case list():
                content["data"] = {self.name.plural: data, "count": len(data)}
            case _:
                content["data"] = {self.name.singular: data}

        return content

    def ok(self) -> dict[str, Any]:
        return self._response(200, data=None)

    def not_found(self, e: DoesNotExistError) -> dict[str, Any]:
        name = self.name.singular.capitalize()

        return self._response(
            404,
            data={"id": str(e.id)},
            error=f"An item<{name}> with id<{e.id}> does not exist.",
        )

    def exists(self, e: ExistsError) -> dict[str, Any]:
        name = self.name.singular.capitalize()

        return self._response(
            409,
            data={"id": str(e.id)},
            error=f"An item<{name}> with the {e} already exists.",
        )

    def created_one(self, item: Any) -> dict[str, Any]:
        return self._response(201, item)

    def created_many(self, items: Iterable[Any]) -> dict[str, Any]:
        return self._response(201, list(items))

    def found_one(self, item: Any) -> dict[str, Any]:
        return self._response(200, item)

    def found_many(self, items: list[Any]) -> dict[str, Any]:
        return self._response(200, items)


T = TypeVar("T")


@dataclass
class RestfulRouter:
    schema: RestfulSchema = field(init=False)
    response: RestfulResponse = field(init=False)
    service: RestfulService = field(init=False)

    router: APIRouter = field(init=False, default_factory=APIRouter)

    @classmethod
    def from_dataclass(cls, value: Any) -> "RestfulRouter":
        return (
            cls()
            .with_schema(RestfulSchema.from_dataclass(value))
            .with_response(RestfulResponse.from_dataclass(value))
        )

    def with_schema(self, value: RestfulSchema) -> Self:
        self.schema = value

        return self

    def with_response(self, value: RestfulResponse) -> Self:
        self.response = value

        return self

    def with_service(self, value: RestfulService) -> Self:
        self.service = value

        return self

    def with_create_one_endpoint(self, is_documented: bool = True) -> Self:
        schema = self.schema.for_create_one()

        @self.router.post(
            "",
            status_code=201,
            responses={409: {}},
            response_model=self.schema.for_item(),
            include_in_schema=is_documented,
        )
        def create_one(item: Annotated[RawItem, Depends(schema)]) -> _Response:
            try:
                item = self.service.create_one(item)
            except ExistsError as e:
                return JSONResponse(self.response.exists(e), 409)

            return self.response.created_one(item)

        return self

    def with_create_many_endpoint(self, is_documented: bool = True) -> Self:
        schema = self.schema.for_create_many()

        @self.router.post(
            "/batch",
            status_code=201,
            responses={409: {}},
            response_model=self.schema.for_collection(),
            include_in_schema=is_documented,
        )
        def create_many(items: Annotated[RawCollection, Depends(schema)]) -> _Response:
            try:
                return self.response.created_many(self.service.create_many(items))
            except ExistsError as e:
                return JSONResponse(self.response.exists(e), 409)

        return self

    def with_read_one_endpoint(self, is_documented: bool = True) -> Self:
        schema = self.schema.for_item()

        @self.router.get(
            "/{item_id}",
            status_code=200,
            responses={404: {}},
            response_model=schema,
            include_in_schema=is_documented,
        )
        def read_one(item_id: str) -> _Response:
            try:
                return self.response.found_one(self.service.read_one(item_id))
            except DoesNotExistError as e:
                return JSONResponse(self.response.not_found(e), 404)

        return self

    def with_read_all_endpoint(self, is_documented: bool = True) -> Self:
        schema = self.schema.for_collection()

        @self.router.get(
            "",
            status_code=200,
            responses={},
            response_model=schema,
            include_in_schema=is_documented,
        )
        def read_all() -> _Response:
            return self.response.found_many(list(self.service.read_all()))

        return self

    def with_update_one_endpoint(self, is_documented: bool = True) -> Self:
        schema = self.schema.for_update_one()

        @self.router.patch(
            "/{item_id}",
            status_code=200,
            responses={404: {}},
            response_model=self.schema.for_no_data(),
            include_in_schema=is_documented,
        )
        def update_one(
            item_id: str,
            updates: Annotated[RawItem, Depends(schema)],
        ) -> _Response:
            try:
                self.service.update_one(item_id, **updates)
            except DoesNotExistError as e:
                return JSONResponse(self.response.not_found(e), 404)

            return self.response.ok()

        return self

    def with_update_many_endpoint(self, is_documented: bool = True) -> Self:
        schema = self.schema.for_update_many()

        @self.router.patch(
            "",
            status_code=200,
            responses={},
            response_model=self.schema.for_no_data(),
            include_in_schema=is_documented,
        )
        def update_many(items: Annotated[RawCollection, Depends(schema)]) -> _Response:
            self.service.update_many(items)

            return self.response.ok()

        return self

    def with_delete_one_endpoint(self, is_documented: bool = True) -> Self:
        schema = self.schema.for_no_data()

        @self.router.delete(
            "/{item_id}",
            status_code=200,
            responses={404: {}},
            response_model=schema,
            include_in_schema=is_documented,
        )
        def delete_one(item_id: str) -> _Response:
            try:
                self.service.delete_one(item_id)
            except DoesNotExistError as e:
                return JSONResponse(self.response.not_found(e), 404)

            return self.response.ok()

        return self

    def default(self) -> Self:
        return (
            self.with_create_one_endpoint()
            .with_create_many_endpoint()
            .with_read_one_endpoint()
            .with_read_all_endpoint()
            .with_update_one_endpoint()
            .with_update_many_endpoint()
            .with_delete_one_endpoint()
        )

    def build(self) -> APIRouter:
        return self.router

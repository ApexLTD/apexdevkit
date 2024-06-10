from dataclasses import dataclass, field
from functools import cached_property
from typing import Annotated, Any, Iterable, Protocol, Self, TypeVar

from fastapi import APIRouter, Depends, Path
from fastapi.responses import JSONResponse

from apexdevkit.error import DoesNotExistError, ExistsError, ForbiddenError
from apexdevkit.fastapi.schema import DataclassFields, RestfulSchema, SchemaFields
from apexdevkit.fastapi.service import RawCollection, RawItem, RestfulService
from apexdevkit.testing import RestfulName

_Response = JSONResponse | dict[str, Any]


@dataclass
class RestfulResponse:
    name: RestfulName

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

    def forbidden(self, e: ForbiddenError) -> dict[str, Any]:
        return self._response(
            403,
            data={"id": str(e.id)},
            error="Forbidden",
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


class RestfulServiceInfra(Protocol):
    def service_for(self, parent_id: str) -> RestfulService:
        pass


@dataclass(frozen=True)
class SingleRestfulServiceInfra:
    service: RestfulService

    def service_for(self, parent_id: str) -> RestfulService:
        return self.service


@dataclass
class RestfulRouter:
    service: RestfulService | None = None

    router: APIRouter = field(default_factory=APIRouter)

    name: RestfulName = field(init=False)
    fields: SchemaFields = field(init=False)
    infra: RestfulServiceInfra = field(init=False)

    parent: str = field(init=False, default="")

    def __post_init__(self) -> None:
        if self.service:
            self.infra = SingleRestfulServiceInfra(self.service)

    @cached_property
    def response(self) -> RestfulResponse:
        return RestfulResponse(name=self.name)

    @cached_property
    def schema(self) -> RestfulSchema:
        return RestfulSchema(name=self.name, fields=self.fields)

    @property
    def id_alias(self) -> str:
        return self.name.singular + "_id"

    @property
    def parent_id_alias(self) -> str:
        return self.parent + "_id"

    @property
    def item_path(self) -> str:
        return "/{" + self.id_alias + "}"

    def with_dataclass(self, value: Any) -> Self:
        return self.with_name(RestfulName(value.__name__.lower())).with_fields(
            DataclassFields(value)
        )

    def with_name(self, value: RestfulName) -> Self:
        self.name = value

        return self

    def with_fields(self, value: SchemaFields) -> Self:
        self.fields = value

        return self

    def with_parent(self, name: str) -> Self:
        self.parent = name

        return self

    def with_service(self, value: RestfulService) -> Self:
        self.infra = SingleRestfulServiceInfra(value)

        return self

    def with_infra(self, value: RestfulServiceInfra) -> Self:
        self.infra = value

        return self

    def with_create_one_endpoint(self, is_documented: bool = True) -> Self:
        parent_id_type = Annotated[
            str,
            Path(alias=self.parent_id_alias, default_factory=str),
        ]

        item_type = Annotated[
            RawItem,
            Depends(self.schema.for_create_one()),
        ]

        @self.router.post(
            "",
            status_code=201,
            responses={409: {}},
            response_model=self.schema.for_item(),
            include_in_schema=is_documented,
        )
        def create_one(parent_id: parent_id_type, item: item_type) -> _Response:
            try:
                service = self.infra.service_for(parent_id)
            except DoesNotExistError as e:
                return JSONResponse(
                    RestfulResponse(RestfulName(self.parent)).not_found(e), 404
                )

            try:
                item = service.create_one(item)
            except ExistsError as e:
                return JSONResponse(self.response.exists(e), 409)

            return self.response.created_one(item)

        return self

    def with_create_many_endpoint(self, is_documented: bool = True) -> Self:
        parent_id_type = Annotated[
            str,
            Path(alias=self.parent_id_alias, default_factory=str),
        ]

        collection_type = Annotated[
            RawCollection,
            Depends(self.schema.for_create_many()),
        ]

        @self.router.post(
            "/batch",
            status_code=201,
            responses={409: {}},
            response_model=self.schema.for_collection(),
            include_in_schema=is_documented,
        )
        def create_many(parent_id: parent_id_type, items: collection_type) -> _Response:
            try:
                service = self.infra.service_for(parent_id)
            except DoesNotExistError as e:
                return JSONResponse(
                    RestfulResponse(RestfulName(self.parent)).not_found(e), 404
                )

            try:
                return self.response.created_many(service.create_many(items))
            except ExistsError as e:
                return JSONResponse(self.response.exists(e), 409)

        return self

    def with_read_one_endpoint(self, is_documented: bool = True) -> Self:
        id_type = Annotated[str, Path(alias=self.id_alias)]
        parent_id_type = Annotated[
            str,
            Path(alias=self.parent_id_alias, default_factory=str),
        ]

        @self.router.get(
            self.item_path,
            status_code=200,
            responses={404: {}},
            response_model=self.schema.for_item(),
            include_in_schema=is_documented,
        )
        def read_one(parent_id: parent_id_type, item_id: id_type) -> _Response:
            service = self.infra.service_for(parent_id)

            try:
                return self.response.found_one(service.read_one(item_id))
            except DoesNotExistError as e:
                return JSONResponse(self.response.not_found(e), 404)

        return self

    def with_read_all_endpoint(self, is_documented: bool = True) -> Self:
        parent_id_type = Annotated[
            str,
            Path(alias=self.parent_id_alias, default_factory=str),
        ]

        @self.router.get(
            "",
            status_code=200,
            responses={},
            response_model=self.schema.for_collection(),
            include_in_schema=is_documented,
        )
        def read_all(parent_id: parent_id_type) -> _Response:
            service = self.infra.service_for(parent_id)

            return self.response.found_many(list(service.read_all()))

        return self

    def with_update_one_endpoint(self, is_documented: bool = True) -> Self:
        parent_id_type = Annotated[
            str,
            Path(alias=self.parent_id_alias, default_factory=str),
        ]
        id_type = Annotated[str, Path(alias=self.id_alias)]
        update_type = Annotated[
            RawItem,
            Depends(self.schema.for_update_one()),
        ]

        @self.router.patch(
            self.item_path,
            status_code=200,
            responses={404: {}},
            response_model=self.schema.for_no_data(),
            include_in_schema=is_documented,
        )
        def update_one(
            parent_id: parent_id_type,
            item_id: id_type,
            updates: update_type,
        ) -> _Response:
            service = self.infra.service_for(parent_id)

            try:
                service.update_one(item_id, **updates)
            except DoesNotExistError as e:
                return JSONResponse(self.response.not_found(e), 404)
            except ForbiddenError as e:
                return JSONResponse(self.response.forbidden(e), 403)

            return self.response.ok()

        return self

    def with_update_many_endpoint(self, is_documented: bool = True) -> Self:
        parent_id_type = Annotated[
            str,
            Path(alias=self.parent_id_alias, default_factory=str),
        ]
        collection_type = Annotated[
            RawCollection,
            Depends(self.schema.for_update_many()),
        ]

        @self.router.patch(
            "",
            status_code=200,
            responses={},
            response_model=self.schema.for_no_data(),
            include_in_schema=is_documented,
        )
        def update_many(parent_id: parent_id_type, items: collection_type) -> _Response:
            service = self.infra.service_for(parent_id)

            service.update_many(items)

            return self.response.ok()

        return self

    def with_delete_one_endpoint(self, is_documented: bool = True) -> Self:
        parent_id_type = Annotated[
            str,
            Path(alias=self.parent_id_alias, default_factory=str),
        ]
        id_type = Annotated[str, Path(alias=self.id_alias)]

        @self.router.delete(
            self.item_path,
            status_code=200,
            responses={404: {}},
            response_model=self.schema.for_no_data(),
            include_in_schema=is_documented,
        )
        def delete_one(parent_id: parent_id_type, item_id: id_type) -> _Response:
            service = self.infra.service_for(parent_id)

            try:
                service.delete_one(item_id)
            except DoesNotExistError as e:
                return JSONResponse(self.response.not_found(e), 404)

            return self.response.ok()

        return self

    def with_sub_resource(self, **names: APIRouter) -> Self:
        for name, router in names.items():
            self.router.include_router(router, prefix=f"{self.item_path}/{name}")

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

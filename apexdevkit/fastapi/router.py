from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from functools import cached_property
from typing import Annotated, Any, Callable, Iterable, Self, TypeVar

from fastapi import APIRouter, Depends, Path
from fastapi.requests import Request
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


@dataclass
class RestfulServiceBuilder(ABC):
    parent_id: str = field(init=False)
    user: Any = field(init=False)

    def with_user(self, user: Any) -> "RestfulServiceBuilder":
        self.user = user

        return self

    def with_parent(self, identity: str) -> "RestfulServiceBuilder":
        self.parent_id = identity

        return self

    @abstractmethod
    def build(self) -> RestfulService:
        pass


@dataclass
class PreBuiltRestfulService(RestfulServiceBuilder):
    service: RestfulService

    def build(self) -> RestfulService:
        return self.service


def no_user(request: Request) -> None:
    pass


@dataclass
class RestfulRouter:
    service: RestfulService | None = None

    router: APIRouter = field(default_factory=APIRouter)

    name: RestfulName = field(init=False)
    fields: SchemaFields = field(init=False)
    infra: RestfulServiceBuilder = field(init=False)

    parent: str = field(init=False, default="")

    def __post_init__(self) -> None:
        if self.service:
            self.infra = PreBuiltRestfulService(self.service)

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
        self.infra = PreBuiltRestfulService(value)

        return self

    def with_infra(self, value: RestfulServiceBuilder) -> Self:
        self.infra = value

        return self

    def with_create_one_endpoint(
        self,
        is_documented: bool = True,
        extract_user: Callable[[Request], Any] = no_user,
    ) -> Self:
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
        def create_one(
            user: Annotated[Any, Depends(extract_user)],
            parent_id: parent_id_type,
            item: item_type,
        ) -> _Response:
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

            return self.response.created_one(item)

        return self

    def with_create_many_endpoint(
        self,
        is_documented: bool = True,
        extract_user: Callable[[Request], Any] = no_user,
    ) -> Self:
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
        def create_many(
            user: Annotated[Any, Depends(extract_user)],
            parent_id: parent_id_type,
            items: collection_type,
        ) -> _Response:
            try:
                service = self.infra.with_user(user).with_parent(parent_id).build()
            except DoesNotExistError as e:
                return JSONResponse(
                    RestfulResponse(RestfulName(self.parent)).not_found(e), 404
                )

            try:
                return self.response.created_many(service.create_many(items))
            except ExistsError as e:
                return JSONResponse(self.response.exists(e), 409)

        return self

    def with_read_one_endpoint(
        self,
        is_documented: bool = True,
        extract_user: Callable[[Request], Any] = no_user,
    ) -> Self:
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
        def read_one(
            user: Annotated[Any, Depends(extract_user)],
            parent_id: parent_id_type,
            item_id: id_type,
        ) -> _Response:
            try:
                service = self.infra.with_user(user).with_parent(parent_id).build()
            except DoesNotExistError as e:
                return JSONResponse(
                    RestfulResponse(RestfulName(self.parent)).not_found(e), 404
                )

            try:
                return self.response.found_one(service.read_one(item_id))
            except DoesNotExistError as e:
                return JSONResponse(self.response.not_found(e), 404)

        return self

    def with_read_all_endpoint(
        self,
        is_documented: bool = True,
        extract_user: Callable[[Request], Any] = no_user,
    ) -> Self:
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
        def read_all(
            user: Annotated[Any, Depends(extract_user)],
            parent_id: parent_id_type,
        ) -> _Response:
            try:
                service = self.infra.with_user(user).with_parent(parent_id).build()
            except DoesNotExistError as e:
                return JSONResponse(
                    RestfulResponse(RestfulName(self.parent)).not_found(e), 404
                )

            return self.response.found_many(list(service.read_all()))

        return self

    def with_update_one_endpoint(
        self,
        is_documented: bool = True,
        extract_user: Callable[[Request], Any] = no_user,
    ) -> Self:
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
            user: Annotated[Any, Depends(extract_user)],
            parent_id: parent_id_type,
            item_id: id_type,
            updates: update_type,
        ) -> _Response:
            try:
                service = self.infra.with_user(user).with_parent(parent_id).build()
            except DoesNotExistError as e:
                return JSONResponse(
                    RestfulResponse(RestfulName(self.parent)).not_found(e), 404
                )
            try:
                service.update_one(item_id, **updates)
            except DoesNotExistError as e:
                return JSONResponse(self.response.not_found(e), 404)
            except ForbiddenError as e:
                return JSONResponse(self.response.forbidden(e), 403)

            return self.response.ok()

        return self

    def with_update_many_endpoint(
        self,
        is_documented: bool = True,
        extract_user: Callable[[Request], Any] = no_user,
    ) -> Self:
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
        def update_many(
            user: Annotated[Any, Depends(extract_user)],
            parent_id: parent_id_type,
            items: collection_type,
        ) -> _Response:
            try:
                service = self.infra.with_user(user).with_parent(parent_id).build()
            except DoesNotExistError as e:
                return JSONResponse(
                    RestfulResponse(RestfulName(self.parent)).not_found(e), 404
                )

            service.update_many(items)

            return self.response.ok()

        return self

    def with_delete_one_endpoint(
        self,
        is_documented: bool = True,
        extract_user: Callable[[Request], Any] = no_user,
    ) -> Self:
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
        def delete_one(
            user: Annotated[Any, Depends(extract_user)],
            parent_id: parent_id_type,
            item_id: id_type,
        ) -> _Response:
            service = self.infra.with_user(user).with_parent(parent_id).build()

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

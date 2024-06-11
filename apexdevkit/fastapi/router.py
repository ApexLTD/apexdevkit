from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from functools import cached_property
from typing import Annotated, Any, Callable, Iterable, Self, TypeVar

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


def no_user() -> None:
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
        extract_user: Callable[..., Any] = no_user,
    ) -> Self:
        self.router.add_api_route(
            "",
            self.create_one(
                User=Annotated[
                    Any,
                    Depends(extract_user),
                ],
                ParentId=Annotated[
                    str,
                    Path(alias=self.parent_id_alias, default_factory=str),
                ],
                Item=Annotated[
                    RawItem,
                    Depends(self.schema.for_create_one()),
                ],
            ),
            methods=["POST"],
            status_code=201,
            responses={409: {}},
            response_model=self.schema.for_item(),
            include_in_schema=is_documented,
            summary="Create One",
        )

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

            return self.response.created_one(item)

        return endpoint

    def with_create_many_endpoint(
        self,
        is_documented: bool = True,
        extract_user: Callable[..., Any] = no_user,
    ) -> Self:
        self.router.add_api_route(
            "/batch",
            self.create_many(
                User=Annotated[
                    Any,
                    Depends(extract_user),
                ],
                ParentId=Annotated[
                    str,
                    Path(alias=self.parent_id_alias, default_factory=str),
                ],
                Collection=Annotated[
                    RawCollection,
                    Depends(self.schema.for_create_many()),
                ],
            ),
            methods=["POST"],
            status_code=201,
            responses={409: {}},
            response_model=self.schema.for_collection(),
            include_in_schema=is_documented,
            summary="Create Many",
        )

        return self

    def create_many(self, User, ParentId, Collection) -> Callable[..., _Response]:  # type: ignore
        def endpoint(user: User, parent_id: ParentId, items: Collection) -> _Response:
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

        return endpoint

    def with_read_one_endpoint(
        self,
        is_documented: bool = True,
        extract_user: Callable[..., Any] = no_user,
    ) -> Self:
        self.router.add_api_route(
            self.item_path,
            self.read_one(
                User=Annotated[
                    Any,
                    Depends(extract_user),
                ],
                ParentId=Annotated[
                    str,
                    Path(alias=self.parent_id_alias, default_factory=str),
                ],
                ItemId=Annotated[
                    str,
                    Path(alias=self.id_alias),
                ],
            ),
            methods=["GET"],
            status_code=200,
            responses={404: {}},
            response_model=self.schema.for_item(),
            include_in_schema=is_documented,
            summary="Read One",
        )

        return self

    def read_one(self, User, ParentId, ItemId) -> Callable[..., _Response]:  # type: ignore
        def endpoint(user: User, parent_id: ParentId, item_id: ItemId) -> _Response:
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

        return endpoint

    def with_read_all_endpoint(
        self,
        is_documented: bool = True,
        extract_user: Callable[..., Any] = no_user,
    ) -> Self:
        self.router.add_api_route(
            "",
            self.read_all(
                User=Annotated[
                    Any,
                    Depends(extract_user),
                ],
                ParentId=Annotated[
                    str,
                    Path(alias=self.parent_id_alias, default_factory=str),
                ],
            ),
            methods=["GET"],
            status_code=200,
            responses={},
            response_model=self.schema.for_collection(),
            include_in_schema=is_documented,
            summary="Read All",
        )

        return self

    def read_all(self, User, ParentId) -> Callable[..., _Response]:  # type: ignore
        def endpoint(user: User, parent_id: ParentId) -> _Response:
            try:
                service = self.infra.with_user(user).with_parent(parent_id).build()
            except DoesNotExistError as e:
                return JSONResponse(
                    RestfulResponse(RestfulName(self.parent)).not_found(e), 404
                )

            return self.response.found_many(list(service.read_all()))

        return endpoint

    def with_update_one_endpoint(
        self,
        is_documented: bool = True,
        extract_user: Callable[..., Any] = no_user,
    ) -> Self:
        self.router.add_api_route(
            self.item_path,
            self.update_one(
                User=Annotated[
                    Any,
                    Depends(extract_user),
                ],
                ParentId=Annotated[
                    str,
                    Path(alias=self.parent_id_alias, default_factory=str),
                ],
                ItemId=Annotated[
                    str,
                    Path(alias=self.id_alias),
                ],
                Updates=Annotated[
                    RawItem,
                    Depends(self.schema.for_update_one()),
                ],
            ),
            methods=["PATCH"],
            status_code=200,
            responses={404: {}},
            response_model=self.schema.for_no_data(),
            include_in_schema=is_documented,
            summary="Update One",
        )

        return self

    def update_one(self, User, ParentId, ItemId, Updates) -> Callable[..., _Response]:  # type: ignore
        def endpoint(
            user: User,
            parent_id: ParentId,
            item_id: ItemId,
            updates: Updates,
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

        return endpoint

    def with_update_many_endpoint(
        self,
        is_documented: bool = True,
        extract_user: Callable[..., Any] = no_user,
    ) -> Self:
        self.router.add_api_route(
            "",
            self.update_many(
                User=Annotated[
                    Any,
                    Depends(extract_user),
                ],
                ParentId=Annotated[
                    str,
                    Path(alias=self.parent_id_alias, default_factory=str),
                ],
                Collection=Annotated[
                    RawCollection,
                    Depends(self.schema.for_update_many()),
                ],
            ),
            methods=["PATCH"],
            status_code=200,
            responses={},
            response_model=self.schema.for_no_data(),
            include_in_schema=is_documented,
            summary="Update Many",
        )

        return self

    def update_many(self, User, ParentId, Collection) -> Callable[..., _Response]:  # type: ignore
        def endpoint(user: User, parent_id: ParentId, items: Collection) -> _Response:
            try:
                service = self.infra.with_user(user).with_parent(parent_id).build()
            except DoesNotExistError as e:
                return JSONResponse(
                    RestfulResponse(RestfulName(self.parent)).not_found(e), 404
                )
            try:
                service.update_many(items)
            except DoesNotExistError as e:
                return JSONResponse(self.response.not_found(e), 404)

            return self.response.ok()

        return endpoint

    def with_delete_one_endpoint(
        self,
        is_documented: bool = True,
        extract_user: Callable[..., Any] = no_user,
    ) -> Self:
        self.router.add_api_route(
            self.item_path,
            self.delete_one(
                User=Annotated[
                    Any,
                    Depends(extract_user),
                ],
                ParentId=Annotated[
                    str,
                    Path(alias=self.parent_id_alias, default_factory=str),
                ],
                ItemId=Annotated[
                    str,
                    Path(alias=self.id_alias),
                ],
            ),
            methods=["DELETE"],
            status_code=200,
            responses={404: {}},
            response_model=self.schema.for_no_data(),
            include_in_schema=is_documented,
            summary="Delete One",
        )

        return self

    def delete_one(self, User, ParentId, ItemId) -> Callable[..., _Response]:  # type: ignore
        def endpoint(user: User, parent_id: ParentId, item_id: ItemId) -> _Response:
            try:
                service = self.infra.with_user(user).with_parent(parent_id).build()
            except DoesNotExistError as e:
                return JSONResponse(
                    RestfulResponse(RestfulName(self.parent)).not_found(e), 404
                )

            try:
                service.delete_one(item_id)
            except DoesNotExistError as e:
                return JSONResponse(self.response.not_found(e), 404)

            return self.response.ok()

        return endpoint

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

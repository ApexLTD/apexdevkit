from dataclasses import dataclass, field
from functools import cached_property
from typing import Annotated, Any, Callable, Self, Type, TypeVar

from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi.responses import JSONResponse

from apexdevkit.error import DoesNotExistError
from apexdevkit.fastapi.builder import RestfulServiceBuilder
from apexdevkit.fastapi.resource import RestfulResource
from apexdevkit.fastapi.response import RestfulResponse
from apexdevkit.fastapi.schema import RestfulSchema, SchemaFields
from apexdevkit.fastapi.service import RawCollection, RawItem, RestfulService
from apexdevkit.testing import RestfulName

_Response = JSONResponse | dict[str, Any]

T = TypeVar("T")


@dataclass
class PreBuiltRestfulService(RestfulServiceBuilder):  # pragma: no cover
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

    parent: str = field(init=False, default="")

    infra: RestfulServiceBuilder = field(init=False)

    def __post_init__(self) -> None:  # pragma: no cover
        if self.service:
            self.with_infra(PreBuiltRestfulService(self.service))

    @cached_property
    def schema(self) -> RestfulSchema:
        return RestfulSchema(name=self.name, fields=self.fields)

    @property
    def resource(self) -> RestfulResource:
        return RestfulResource(self.name)

    @property
    def id_alias(self) -> str:
        return self.name.singular + "_id"

    @property
    def parent_id_alias(self) -> str:
        return self.parent + "_id"

    @property
    def item_path(self) -> str:
        return "/{" + self.id_alias + "}"

    def with_name(self, value: RestfulName) -> Self:
        self.name = value

        return self

    def with_fields(self, value: SchemaFields) -> Self:
        self.fields = value

        return self

    def with_parent(self, name: str) -> Self:
        self.parent = name

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
            self.resource.create_one(
                Service=self._service(extract_user),
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

    def with_create_many_endpoint(
        self,
        is_documented: bool = True,
        extract_user: Callable[..., Any] = no_user,
    ) -> Self:
        self.router.add_api_route(
            "/batch",
            self.resource.create_many(
                Service=self._service(extract_user),
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

    def with_read_one_endpoint(
        self,
        is_documented: bool = True,
        extract_user: Callable[..., Any] = no_user,
    ) -> Self:
        self.router.add_api_route(
            self.item_path,
            self.resource.read_one(
                Service=self._service(extract_user),
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

    def with_read_all_endpoint(
        self,
        is_documented: bool = True,
        extract_user: Callable[..., Any] = no_user,
    ) -> Self:
        self.router.add_api_route(
            "",
            self.resource.read_all(
                Service=self._service(extract_user),
            ),
            methods=["GET"],
            status_code=200,
            responses={},
            response_model=self.schema.for_collection(),
            include_in_schema=is_documented,
            summary="Read All",
        )

        return self

    def with_update_one_endpoint(
        self,
        is_documented: bool = True,
        extract_user: Callable[..., Any] = no_user,
    ) -> Self:
        self.router.add_api_route(
            self.item_path,
            self.resource.update_one(
                Service=self._service(extract_user),
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

    def with_update_many_endpoint(
        self,
        is_documented: bool = True,
        extract_user: Callable[..., Any] = no_user,
    ) -> Self:
        self.router.add_api_route(
            "",
            self.resource.update_many(
                Service=self._service(extract_user),
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

    def with_replace_one_endpoint(
        self,
        is_documented: bool = True,
        extract_user: Callable[..., Any] = no_user,
    ) -> Self:
        self.router.add_api_route(
            "",
            self.resource.replace_one(
                Service=self._service(extract_user),
                Item=Annotated[
                    RawItem,
                    Depends(self.schema.for_replace_one()),
                ],
            ),
            methods=["PUT"],
            status_code=200,
            responses={404: {}},
            response_model=self.schema.for_no_data(),
            include_in_schema=is_documented,
            summary="Replace One",
        )

        return self

    def with_replace_many_endpoint(
        self,
        is_documented: bool = True,
        extract_user: Callable[..., Any] = no_user,
    ) -> Self:
        self.router.add_api_route(
            "/batch",
            self.resource.replace_many(
                Service=self._service(extract_user),
                Collection=Annotated[
                    RawCollection,
                    Depends(self.schema.for_replace_many()),
                ],
            ),
            methods=["PUT"],
            status_code=200,
            responses={},
            response_model=self.schema.for_no_data(),
            include_in_schema=is_documented,
            summary="Replace Many",
        )

        return self

    def with_delete_one_endpoint(
        self,
        is_documented: bool = True,
        extract_user: Callable[..., Any] = no_user,
    ) -> Self:
        self.router.add_api_route(
            self.item_path,
            self.resource.delete_one(
                Service=self._service(extract_user),
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

    def _service(
        self, extract_user: Callable[..., Any] = no_user
    ) -> Type[RestfulService]:
        User = Annotated[Any, Depends(extract_user)]
        ParentId = Annotated[str, Path(alias=self.parent_id_alias)]

        def srv_child(user: User, parent_id: ParentId) -> RestfulService:
            try:
                return self.infra.with_user(user).with_parent(parent_id).build()
            except DoesNotExistError as e:
                raise HTTPException(
                    status_code=404,
                    detail=RestfulResponse(RestfulName(self.parent)).not_found(e),
                )

        def srv_root(user: User) -> RestfulService:
            try:
                return self.infra.with_user(user).build()
            except DoesNotExistError as e:
                raise HTTPException(
                    status_code=404,
                    detail=RestfulResponse(RestfulName(self.parent)).not_found(e),
                )

        if self.parent:
            return Annotated[RestfulService, Depends(srv_child)]  # type: ignore
        else:
            return Annotated[RestfulService, Depends(srv_root)]  # type: ignore

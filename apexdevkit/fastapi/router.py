from dataclasses import dataclass, field
from functools import cached_property
from typing import Annotated, Any, Callable, Protocol, Self, TypeVar

from fastapi import APIRouter, Depends, Path
from fastapi.responses import JSONResponse

from apexdevkit.fastapi.builder import RestfulServiceBuilder
from apexdevkit.fastapi.resource import RestfulResource
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


class _Dependency(Protocol):
    def as_dependable(self, **data: Any) -> type[RestfulServiceBuilder]:
        pass


@dataclass
class ServiceDependency:
    dependency: _Dependency

    def as_dependable(self, **data: Any) -> type[RestfulService]:
        Builder = self.dependency.as_dependable(**data)

        def _(builder: Builder) -> RestfulService:  # type: ignore
            return builder.build()  # type: ignore

        return Annotated[RestfulService, Depends(_)]  # type: ignore


@dataclass
class UserDependency:
    dependency: _Dependency

    def as_dependable(self, **data: Any) -> type[RestfulServiceBuilder]:
        Builder = self.dependency.as_dependable(**data)
        User = Annotated[Any, Depends(data["extract_user"])]

        def _(builder: Builder, user: User) -> RestfulServiceBuilder:  # type: ignore
            return builder.with_user(user)  # type: ignore

        return Annotated[RestfulServiceBuilder, Depends(_)]  # type: ignore


@dataclass
class ParentDependency:
    parent: RestfulName
    dependency: _Dependency

    def as_dependable(self, **data: Any) -> type[RestfulServiceBuilder]:
        Builder = self.dependency.as_dependable(**data)
        ParentId = Annotated[str, Path(alias=self.parent.singular + "_id")]

        def _(builder: Builder, parent_id: ParentId) -> RestfulServiceBuilder:  # type: ignore
            return builder.with_parent(parent_id)  # type: ignore

        return Annotated[RestfulServiceBuilder, Depends(_)]  # type: ignore


@dataclass
class InfraDependency:
    infra: RestfulServiceBuilder

    def as_dependable(self, **data: Any) -> type[RestfulServiceBuilder]:
        def _() -> RestfulServiceBuilder:
            return self.infra

        return Annotated[RestfulServiceBuilder, Depends(_)]  # type: ignore


@dataclass
class RestfulRouter:
    router: APIRouter = field(default_factory=APIRouter)

    name: RestfulName = field(init=False)
    fields: SchemaFields = field(init=False)

    _dependable: _Dependency = field(init=False)

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
    def item_path(self) -> str:
        return "/{" + self.id_alias + "}"

    def _dependable_with(
        self, extract_user: Callable[..., Any]
    ) -> type[RestfulServiceBuilder]:
        return ServiceDependency(UserDependency(self._dependable)).as_dependable(  # type: ignore
            extract_user=extract_user
        )

    def with_name(self, value: RestfulName) -> Self:
        self.name = value

        return self

    def with_fields(self, value: SchemaFields) -> Self:
        self.fields = value

        return self

    def with_parent(self, name: str) -> Self:
        self._dependable = ParentDependency(RestfulName(name), self._dependable)

        return self

    def with_infra(self, value: RestfulServiceBuilder) -> Self:
        self._dependable = InfraDependency(value)

        return self

    def with_create_one_endpoint(
        self,
        is_documented: bool = True,
        extract_user: Callable[..., Any] = no_user,
    ) -> Self:
        self.router.add_api_route(
            "",
            self.resource.create_one(
                Service=self._dependable_with(extract_user),
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
                Service=self._dependable_with(extract_user),
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
                Service=self._dependable_with(extract_user),
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
                Service=self._dependable_with(extract_user),
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
                Service=self._dependable_with(extract_user),
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
                Service=self._dependable_with(extract_user),
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
                Service=self._dependable_with(extract_user),
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
                Service=self._dependable_with(extract_user),
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
                Service=self._dependable_with(extract_user),
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

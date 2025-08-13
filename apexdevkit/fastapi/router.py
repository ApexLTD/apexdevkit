from dataclasses import dataclass, field
from enum import Enum
from functools import cached_property
from typing import Annotated, Any, Protocol, Self, TypeVar

from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import JSONResponse

from apexdevkit.fastapi.name import RestfulName
from apexdevkit.fastapi.resource import RestfulResource
from apexdevkit.fastapi.response import RestfulResponse
from apexdevkit.fastapi.schema import RestfulSchema, Schema, SchemaFields
from apexdevkit.fastapi.service import RawCollection, RawItem, RestfulService
from apexdevkit.fluent import FluentDict

_Response = JSONResponse | dict[str, Any]

T = TypeVar("T")


class Dependency(Protocol):  # pragma: no cover
    def as_dependable(self) -> type[RestfulService]:
        pass


@dataclass
class RestfulRouter:
    router: APIRouter = field(default_factory=APIRouter)

    name: RestfulName = field(init=False)
    fields: SchemaFields = field(init=False)

    dependency: Dependency | None = None

    @cached_property
    def schema(self) -> RestfulSchema:
        return RestfulSchema(name=self.name, fields=self.fields)

    @property
    def resource(self) -> RestfulResource:
        return RestfulResource(RestfulResponse(self.name))

    @property
    def id_alias(self) -> str:
        return self.name.singular.replace("-", "_") + "_id"

    @property
    def item_path(self) -> str:
        return "/{" + self.id_alias + "}"

    def with_name(self, value: RestfulName) -> Self:
        self.name = value

        return self

    def with_fields(self, value: SchemaFields) -> Self:
        self.fields = value

        return self

    def with_tag(self, value: list[str | Enum]) -> Self:
        self.router.tags = value

        return self

    def with_dependency(self, value: Dependency) -> Self:
        self.dependency = value

        return self

    def with_create_one_endpoint(
        self,
        dependency: Dependency | None = None,
        is_documented: bool = True,
    ) -> Self:
        self.router.add_api_route(
            "",
            self.resource.create_one(
                Service=self._resolve(dependency),
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
        dependency: Dependency | None = None,
        is_documented: bool = True,
    ) -> Self:
        self.router.add_api_route(
            "/batch",
            self.resource.create_many(
                Service=self._resolve(dependency),
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
        dependency: Dependency | None = None,
        is_documented: bool = True,
    ) -> Self:
        self.router.add_api_route(
            self.item_path,
            self.resource.read_one(
                Service=self._resolve(dependency),
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

    def with_read_many_endpoint(
        self,
        query: FluentDict[Any],
        dependency: Dependency | None = None,
        is_documented: bool = True,
    ) -> Self:
        self.router.add_api_route(
            "",
            self.resource.read_many(
                Service=self._resolve(dependency),
                QueryParams=Annotated[
                    Schema(self.name).optional_schema_for("ReadMany", query), Query()
                ],
            ),
            methods=["GET"],
            status_code=200,
            responses={},
            response_model=self.schema.for_collection(),
            include_in_schema=is_documented,
            summary="Read Many",
        )

        return self

    def with_filter_endpoint(
        self,
        dependency: Dependency | None = None,
        is_documented: bool = True,
    ) -> Self:
        self.router.add_api_route(
            "/filter",
            self.resource.filter_with(
                Service=self._resolve(dependency),
                QueryOptions=Annotated[RawItem, Depends(self.schema.for_filters())],
            ),
            methods=["POST"],
            status_code=200,
            responses={},
            response_model=self.schema.for_collection(),
            include_in_schema=is_documented,
            summary="Read Filtered",
        )

        return self

    def with_aggregation_endpoint(
        self,
        dependency: Dependency | None = None,
        is_documented: bool = True,
    ) -> Self:
        self.router.add_api_route(
            "/aggregation",
            self.resource.aggregation_with(
                Service=self._resolve(dependency),
                FilterOptions=Annotated[
                    RawItem, Depends(self.schema.for_aggregation())
                ],
            ),
            methods=["POST"],
            status_code=200,
            responses={},
            response_model=self.schema.for_aggregation_result(),
            include_in_schema=is_documented,
            summary="Aggregation",
        )

        return self

    def with_read_all_endpoint(
        self,
        dependency: Dependency | None = None,
        is_documented: bool = True,
    ) -> Self:
        self.router.add_api_route(
            "",
            self.resource.read_all(Service=self._resolve(dependency)),
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
        dependency: Dependency | None = None,
        is_documented: bool = True,
    ) -> Self:
        self.router.add_api_route(
            self.item_path,
            self.resource.update_one(
                Service=self._resolve(dependency),
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
        dependency: Dependency | None = None,
        is_documented: bool = True,
    ) -> Self:
        self.router.add_api_route(
            "",
            self.resource.update_many(
                Service=self._resolve(dependency),
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
        dependency: Dependency | None = None,
        is_documented: bool = True,
    ) -> Self:
        self.router.add_api_route(
            "",
            self.resource.replace_one(
                Service=self._resolve(dependency),
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
        dependency: Dependency | None = None,
        is_documented: bool = True,
    ) -> Self:
        self.router.add_api_route(
            "/batch",
            self.resource.replace_many(
                Service=self._resolve(dependency),
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
        dependency: Dependency | None = None,
        is_documented: bool = True,
    ) -> Self:
        self.router.add_api_route(
            self.item_path,
            self.resource.delete_one(
                Service=self._resolve(dependency),
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

    def _resolve(self, dependency: Dependency | None) -> type[RestfulService]:
        resolved = dependency or self.dependency
        assert resolved, "One of default or endpoint dependency must be specified"

        return resolved.as_dependable()

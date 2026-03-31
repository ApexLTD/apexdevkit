from dataclasses import dataclass, field
from enum import Enum
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
    name: RestfulName

    parent: RestfulName | None = None
    router: APIRouter = field(default_factory=APIRouter)

    _schema: RestfulSchema = field(init=False)
    _dependency: Dependency | None = field(init=False, default=None)

    @classmethod
    def named(cls, singular: str, *, plural: str | None = None) -> "RestfulRouter":
        if plural:
            return cls(RestfulName(singular, plural))

        return cls(RestfulName(singular))

    def child_of(self, singular: str, *, plural: str | None = None) -> Self:
        self.parent = RestfulName(singular)

        if plural:
            self.parent = RestfulName(singular, plural)

        return self

    @property
    def resource(self) -> RestfulResource:
        return RestfulResource(RestfulResponse(self.name))

    @property
    def id_alias(self) -> str:
        return self.name.singular.replace("-", "_") + "_id"

    @property
    def item_path(self) -> str:
        return "/{" + self.id_alias + "}"

    def with_fields(self, value: SchemaFields) -> Self:
        self._schema = RestfulSchema(
            name=self.name,
            fields=value,
            generator=self._schema_generator,
        )

        return self

    @property
    def _schema_generator(self) -> Schema:
        if self.parent:
            return Schema(
                self.parent.singular.capitalize() + self.name.singular.capitalize()
            )

        return Schema(self.name.singular.capitalize())

    def with_tag(self, value: list[str | Enum]) -> Self:
        self.router.tags = value

        return self

    def with_default_dependency(self, value: Dependency) -> Self:
        self._dependency = value

        return self

    def with_create_one(
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
                    Depends(self._schema.for_create_one()),
                ],
            ),
            methods=["POST"],
            status_code=201,
            responses={409: {}},
            response_model=self._schema.for_item(),
            include_in_schema=is_documented,
            summary="Create One",
        )

        return self

    def with_create_many(
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
                    Depends(self._schema.for_create_many()),
                ],
            ),
            methods=["POST"],
            status_code=201,
            responses={409: {}},
            response_model=self._schema.for_collection(),
            include_in_schema=is_documented,
            summary="Create Many",
        )

        return self

    def with_read_one(
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
            response_model=self._schema.for_item(),
            include_in_schema=is_documented,
            summary="Read One",
        )

        return self

    def with_read_many(
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
                    Schema(self.name.singular).optional_schema_for("ReadMany", query),
                    Query(),
                ],
            ),
            methods=["GET"],
            status_code=200,
            responses={},
            response_model=self._schema.for_collection(),
            include_in_schema=is_documented,
            summary="Read Many",
        )

        return self

    def with_filter(
        self,
        dependency: Dependency | None = None,
        is_documented: bool = True,
    ) -> Self:
        self.router.add_api_route(
            "/filter",
            self.resource.filter_with(
                Service=self._resolve(dependency),
                QueryOptions=Annotated[RawItem, Depends(self._schema.for_filters())],
            ),
            methods=["POST"],
            status_code=200,
            responses={},
            response_model=self._schema.for_collection(),
            include_in_schema=is_documented,
            summary="Read Filtered",
        )

        return self

    def with_aggregation(
        self,
        dependency: Dependency | None = None,
        is_documented: bool = True,
    ) -> Self:
        self.router.add_api_route(
            "/aggregation",
            self.resource.aggregation_with(
                Service=self._resolve(dependency),
                FilterOptions=Annotated[
                    RawItem, Depends(self._schema.for_aggregation())
                ],
            ),
            methods=["POST"],
            status_code=200,
            responses={},
            response_model=self._schema.for_aggregation_result(),
            include_in_schema=is_documented,
            summary="Aggregation",
        )

        return self

    def with_read_all(
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
            response_model=self._schema.for_collection(),
            include_in_schema=is_documented,
            summary="Read All",
        )

        return self

    def with_update_one(
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
                    Depends(self._schema.for_update_one()),
                ],
            ),
            methods=["PATCH"],
            status_code=200,
            responses={404: {}},
            response_model=self._schema.for_no_data(),
            include_in_schema=is_documented,
            summary="Update One",
        )

        return self

    def with_update_many(
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
                    Depends(self._schema.for_update_many()),
                ],
            ),
            methods=["PATCH"],
            status_code=200,
            responses={},
            response_model=self._schema.for_no_data(),
            include_in_schema=is_documented,
            summary="Update Many",
        )

        return self

    def with_replace_one(
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
                    Depends(self._schema.for_replace_one()),
                ],
            ),
            methods=["PUT"],
            status_code=200,
            responses={404: {}},
            response_model=self._schema.for_no_data(),
            include_in_schema=is_documented,
            summary="Replace One",
        )

        return self

    def with_replace_many(
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
                    Depends(self._schema.for_replace_many()),
                ],
            ),
            methods=["PUT"],
            status_code=200,
            responses={},
            response_model=self._schema.for_no_data(),
            include_in_schema=is_documented,
            summary="Replace Many",
        )

        return self

    def with_delete_one(
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
            response_model=self._schema.for_no_data(),
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
            self.with_create_one()
            .with_create_many()
            .with_read_one()
            .with_read_all()
            .with_update_one()
            .with_update_many()
            .with_delete_one()
        )

    def build(self) -> APIRouter:
        return self.router

    def _resolve(self, dependency: Dependency | None) -> type[RestfulService]:
        resolved = dependency or self._dependency
        assert resolved, "One of default or endpoint dependency must be specified"

        return resolved.as_dependable()

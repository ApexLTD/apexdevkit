from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated, Any, Protocol

from fastapi import Depends, Path
from fastapi.requests import Request

from apexdevkit.error import ApiError, DoesNotExistError, ForbiddenError
from apexdevkit.fastapi import RestfulServiceBuilder
from apexdevkit.fastapi.builder import PreBuilt
from apexdevkit.fastapi.name import RestfulName
from apexdevkit.fastapi.response import RestfulResponse
from apexdevkit.fastapi.service import RestfulService


def inject(dependency: str) -> Any:  # pragma: no cover
    def get(request: Request) -> Any:
        return getattr(request.app.state, dependency)

    return Depends(get)


class _Dependency(Protocol):
    def as_dependable(self) -> type[RestfulServiceBuilder]:
        pass


@dataclass(frozen=True)
class ServiceDependency:
    dependency: _Dependency

    def as_dependable(self) -> type[RestfulService]:
        Builder = self.dependency.as_dependable()

        def _(builder: Builder) -> RestfulService:
            try:
                return builder.build()
            except ForbiddenError as e:
                raise ApiError(
                    403, RestfulResponse(RestfulName("unknown")).forbidden(e)
                ) from e

        return Annotated[RestfulService, Depends(_)]


@dataclass(frozen=True)
class ParentDependency:
    parent: RestfulName
    dependency: _Dependency

    def as_dependable(self) -> type[RestfulServiceBuilder]:
        Builder = self.dependency.as_dependable()
        ParentId = Annotated[
            str, Path(alias=self.parent.singular.replace("-", "_") + "_id")
        ]

        def _(builder: Builder, parent_id: ParentId) -> RestfulServiceBuilder:
            try:
                return builder.with_parent(parent_id)
            except DoesNotExistError as e:
                raise ApiError(404, RestfulResponse(self.parent).not_found(e)) from e

        return Annotated[RestfulServiceBuilder, Depends(_)]


@dataclass(frozen=True)
class UserDependency:
    extract_user: Callable[..., Any]
    dependency: _Dependency

    def as_dependable(self) -> type[RestfulServiceBuilder]:
        Builder = self.dependency.as_dependable()
        User = Annotated[Any, Depends(self.extract_user)]

        def _(builder: Builder, user: User) -> RestfulServiceBuilder:
            return builder.with_user(user)

        return Annotated[RestfulServiceBuilder, Depends(_)]


_BuilderCallable = Callable[..., RestfulServiceBuilder]


@dataclass(frozen=True)
class BuilderCallableDependency:
    create_builder: _BuilderCallable

    def as_dependable(self) -> type[RestfulServiceBuilder]:
        def _() -> RestfulServiceBuilder:
            return self.create_builder()

        return Annotated[RestfulServiceBuilder, Depends(_)]


@dataclass(frozen=True)
class DependableBuilder:
    dependency: _Dependency

    @classmethod
    def from_callable(cls, value: _BuilderCallable) -> "DependableBuilder":
        return cls(BuilderCallableDependency(value))

    @classmethod
    def from_builder(cls, value: RestfulServiceBuilder) -> "DependableBuilder":
        return cls(BuilderCallableDependency(lambda: value))

    @classmethod
    def from_service(cls, value: RestfulService) -> "DependableBuilder":
        return cls(BuilderCallableDependency(lambda: PreBuilt(value)))

    def with_parent(self, value: RestfulName) -> "DependableBuilder":
        return DependableBuilder(ParentDependency(value, self.dependency))

    def with_user(self, extract_user: Callable[..., Any]) -> "DependableBuilder":
        return DependableBuilder(UserDependency(extract_user, self.dependency))

    def as_dependable(self) -> type[RestfulService]:
        return ServiceDependency(self.dependency).as_dependable()

from dataclasses import dataclass, field
from typing import Annotated, Any, Callable, Protocol, Self

from fastapi import Depends, Path
from fastapi.requests import Request

from apexdevkit.error import ApiError, DoesNotExistError
from apexdevkit.fastapi import RestfulServiceBuilder
from apexdevkit.fastapi.response import RestfulResponse
from apexdevkit.fastapi.service import RestfulService
from apexdevkit.testing import RestfulName


def inject(dependency: str) -> Any:  # pragma: no cover
    def get(request: Request) -> Any:
        return getattr(request.app.state, dependency)

    return Depends(get)


class _Dependency(Protocol):
    def as_dependable(self) -> type[RestfulServiceBuilder]:
        pass


@dataclass
class ServiceDependency:
    dependency: _Dependency

    def as_dependable(self) -> type[RestfulService]:
        Builder = self.dependency.as_dependable()

        def _(builder: Builder) -> RestfulService:
            return builder.build()

        return Annotated[RestfulService, Depends(_)]


@dataclass
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
                raise ApiError(404, RestfulResponse(self.parent).not_found(e))

        return Annotated[RestfulServiceBuilder, Depends(_)]


@dataclass
class UserDependency:
    extract_user: Callable[..., Any]
    dependency: _Dependency

    def as_dependable(self) -> type[RestfulServiceBuilder]:
        Builder = self.dependency.as_dependable()
        User = Annotated[Any, Depends(self.extract_user)]

        def _(builder: Builder, user: User) -> RestfulServiceBuilder:
            return builder.with_user(user)

        return Annotated[RestfulServiceBuilder, Depends(_)]


@dataclass
class InfraDependency:
    infra: RestfulServiceBuilder

    def as_dependable(self) -> type[RestfulServiceBuilder]:
        def _() -> RestfulServiceBuilder:
            return self.infra

        return Annotated[RestfulServiceBuilder, Depends(_)]


@dataclass
class DependableBuilder:
    dependency: _Dependency = field(init=False)

    def from_infra(self, value: RestfulServiceBuilder) -> Self:
        self.dependency = InfraDependency(value)

        return self

    def with_parent(self, value: RestfulName) -> Self:
        dependable = DependableBuilder()
        dependable.dependency = ParentDependency(value, self.dependency)

        return dependable

    def with_user(self, extract_user: Callable[..., Any]) -> Self:
        dependable = DependableBuilder()
        dependable.dependency = UserDependency(extract_user, self.dependency)

        return dependable

    def as_dependable(self) -> type[RestfulService]:
        return ServiceDependency(self.dependency).as_dependable()

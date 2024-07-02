from dataclasses import dataclass, field
from typing import Annotated, Any, Callable, Protocol, Self

from fastapi import Depends, Path
from fastapi.requests import Request

from apexdevkit.fastapi import RestfulServiceBuilder
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

        def _(builder: Builder) -> RestfulService:  # type: ignore
            return builder.build()  # type: ignore

        return Annotated[RestfulService, Depends(_)]  # type: ignore


@dataclass
class ParentDependency:
    parent: RestfulName
    dependency: _Dependency

    def as_dependable(self) -> type[RestfulServiceBuilder]:
        Builder = self.dependency.as_dependable()
        ParentId = Annotated[str, Path(alias=self.parent.singular + "_id")]

        def _(builder: Builder, parent_id: ParentId) -> RestfulServiceBuilder:  # type: ignore
            return builder.with_parent(parent_id)  # type: ignore

        return Annotated[RestfulServiceBuilder, Depends(_)]  # type: ignore


@dataclass
class UserDependency:
    extract_user: Callable[..., Any]
    dependency: _Dependency

    def as_dependable(self) -> type[RestfulServiceBuilder]:
        Builder = self.dependency.as_dependable()
        User = Annotated[Any, Depends(self.extract_user)]

        def _(builder: Builder, user: User) -> RestfulServiceBuilder:  # type: ignore
            return builder.with_user(user)  # type: ignore

        return Annotated[RestfulServiceBuilder, Depends(_)]  # type: ignore


@dataclass
class InfraDependency:
    infra: RestfulServiceBuilder

    def as_dependable(self) -> type[RestfulServiceBuilder]:
        def _() -> RestfulServiceBuilder:
            return self.infra

        return Annotated[RestfulServiceBuilder, Depends(_)]  # type: ignore


@dataclass
class DependableBuilder:
    dependency: _Dependency = field(init=False)

    def with_infra(self, value: RestfulServiceBuilder) -> Self:
        self.dependency = InfraDependency(value)

        return self

    def with_parent(self, value: RestfulName) -> Self:
        self.dependency = ParentDependency(value, self.dependency)

        return self

    def build(self, extract_user: Callable[..., Any]) -> type[RestfulService]:
        return ServiceDependency(
            UserDependency(extract_user, self.dependency)
        ).as_dependable()

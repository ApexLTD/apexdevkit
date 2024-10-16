from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Self

from fastapi import APIRouter, FastAPI
from starlette.responses import JSONResponse

from apexdevkit.error import ApiError
from apexdevkit.fastapi.service import RestfulService


@dataclass
class FastApiBuilder:
    app: FastAPI = field(default_factory=FastAPI)

    def build(self) -> FastAPI:
        self.app.add_exception_handler(
            ApiError,
            lambda request, exc: JSONResponse(content=exc.data, status_code=exc.code),
        )
        return self.app

    def with_title(self, value: str) -> Self:
        self.app.title = value

        return self

    def with_description(self, value: str) -> Self:
        self.app.description = value

        return self

    def with_version(self, value: str) -> Self:
        self.app.version = value

        return self

    def with_dependency(self, **values: Any) -> Self:  # pragma: no cover
        for key, value in values.items():
            setattr(self.app.state, key, value)

        return self

    def with_route(self, **values: APIRouter) -> Self:
        for key, value in values.items():
            self.app.include_router(value, prefix=f"/{key}", tags=[key.title()])

        return self


@dataclass
class RestfulServiceBuilder(ABC):
    parent_id: str = field(init=False)
    user: Any = field(init=False)

    def with_user(self, user: Any) -> RestfulServiceBuilder:
        self.user = user

        return self

    def with_parent(self, identity: str) -> RestfulServiceBuilder:
        self.parent_id = identity

        return self

    @abstractmethod
    def build(self) -> RestfulService:  # pragma: no cover
        pass

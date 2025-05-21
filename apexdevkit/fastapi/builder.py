from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Self

from fastapi import APIRouter, FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from apexdevkit.error import ApiError
from apexdevkit.fastapi.service import RestfulService


@dataclass
class FastApiBuilder:
    app: FastAPI = field(default_factory=FastAPI)

    def build(self) -> FastAPI:
        self.app.add_exception_handler(
            ApiError,
            lambda _, exc: JSONResponse(content=exc.data, status_code=exc.code),
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
        return self.with_routes(values)

    def with_routes(self, values: Mapping[str, APIRouter]) -> Self:
        for key, value in values.items():
            self.app.include_router(
                value, prefix=f"/{key}", tags=value.tags or [key.title()]
            )

        return self

    def with_mounted(self, **apps: FastAPI) -> Self:
        for path, app in apps.items():
            self.app.mount(f"/{path.replace('_', '-')}", app)

        return self

    def with_frontend(self, origin: str) -> Self:
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=[origin],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        return self

    def with_swagger(self, **config: Any) -> Self:
        self.app.swagger_ui_parameters = config

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


@dataclass
class PreBuilt(RestfulServiceBuilder):  # pragma: no cover
    service: RestfulService

    def build(self) -> RestfulService:
        return self.service

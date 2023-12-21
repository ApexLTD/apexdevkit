from dataclasses import dataclass, field
from typing import Any, Self

from fastapi import APIRouter, FastAPI


@dataclass
class FastApiBuilder:
    app: FastAPI = field(default_factory=FastAPI)

    def build(self) -> FastAPI:
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

    def with_dependency(self, **values: Any) -> Self:
        for key, value in values.items():
            setattr(self.app.state, key, value)

        return self

    def with_route(self, **values: APIRouter) -> Self:
        for key, value in values.items():
            self.app.include_router(value, prefix=f"/{key}", tags=[key.title()])

        return self

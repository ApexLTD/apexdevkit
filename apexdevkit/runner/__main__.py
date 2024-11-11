from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import uvicorn
from fastapi import FastAPI

from apexdevkit.fastapi import FastApiBuilder, RestfulServiceBuilder
from apexdevkit.fastapi.dependable import DependableBuilder
from apexdevkit.fastapi.name import RestfulName
from apexdevkit.fastapi.router import RestfulRouter
from apexdevkit.fastapi.service import RawCollection, RestfulService
from apexdevkit.http import JsonDict
from tests.resource.sample_api import AppleFields, Color


@dataclass
class AppleRestfulService(RestfulService):
    def read_many(self, **params: Any) -> RawCollection:
        print(params)
        return [
            {"id": "5", "name": {"apple", "apple"}, "color": Color[params["color"]]}
        ]

    @dataclass
    class Builder(RestfulServiceBuilder):
        def build(self) -> RestfulService:
            return AppleRestfulService()


def setup() -> FastAPI:
    return (
        FastApiBuilder()
        .with_title("Apex Payment Service")
        .with_description("Apex Payment Service")
        .with_version("0.0.0")
        .with_route(
            orders=RestfulRouter()
            .with_name(RestfulName("apple"))
            .with_fields(AppleFields())
            .with_read_many_endpoint(
                dependency=DependableBuilder().from_infra(
                    AppleRestfulService.Builder()
                ),
                query=JsonDict().with_a(color=str),
            )
            .build()
        )
        .build()
    )


if __name__ == "__main__":
    uvicorn.run(
        host="0.0.0.0",
        port=8000,
        root_path="",
        app=setup(),
    )

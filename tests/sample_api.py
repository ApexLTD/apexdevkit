from __future__ import annotations

from fastapi import FastAPI

from apexdevkit.fastapi import FastApiBuilder
from apexdevkit.fastapi.router import RestfulRouter
from apexdevkit.fastapi.service import InMemoryRestfulService
from apexdevkit.repository import InMemoryRepository
from apexdevkit.repository.in_memory import DataclassFormatter
from tests.test_rest_resource import Apple


def setup() -> FastAPI:
    apple_service = InMemoryRestfulService(
        Apple,
        InMemoryRepository[Apple](DataclassFormatter[Apple](Apple)).with_unique(
            criteria=lambda item: f"name<{item.name}>"
        ),
    )

    return (
        FastApiBuilder()
        .with_title("Apple API")
        .with_version("1.0.0")
        .with_description("Sample API for unit testing various testing routines")
        .with_route(
            apples=(
                RestfulRouter.from_dataclass(Apple)
                .with_service(apple_service)
                .default()
                .build()
            )
        )
        .build()
    )

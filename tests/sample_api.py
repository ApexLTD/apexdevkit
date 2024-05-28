from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from fastapi import FastAPI

from apexdevkit.fastapi import FastApiBuilder
from apexdevkit.fastapi.router import RestfulRouter
from apexdevkit.fastapi.service import RestfulRepository
from apexdevkit.repository import InMemoryRepository


def setup() -> FastAPI:
    return (
        FastApiBuilder()
        .with_title("Apple API")
        .with_version("1.0.0")
        .with_description("Sample API for unit testing various testing routines")
        .with_route(
            apples=RestfulRouter(
                service=RestfulRepository(
                    Apple,
                    InMemoryRepository[Apple]
                    .for_dataclass(Apple)
                    .with_unique(criteria=lambda item: f"name<{item.name}>"),
                )
            )
            .with_dataclass(Apple)
            .default()
            .build()
        )
        .build()
    )


@dataclass(frozen=True)
class Apple:
    color: str
    name: str

    id: str = field(default_factory=lambda: str(uuid4()))

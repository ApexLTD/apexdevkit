from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4

from fastapi import FastAPI

from apexdevkit.fastapi import FastApiBuilder
from apexdevkit.fastapi.router import RestfulRouter
from apexdevkit.fastapi.schema import SchemaFields
from apexdevkit.fastapi.service import RestfulRepository
from apexdevkit.http import JsonDict
from apexdevkit.repository import InMemoryRepository
from apexdevkit.testing import RestfulName


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
            .with_name(RestfulName("apple"))
            .with_fields(AppleFields())
            .default()
            .build()
        )
        .build()
    )


class Color(Enum):
    red = "RED"
    gold = "GOLD"


@dataclass(frozen=True)
class Apple:
    name: str
    color: Color

    id: str = field(default_factory=lambda: str(uuid4()))


class AppleFields(SchemaFields):
    def readable(self) -> JsonDict:
        return JsonDict().with_a(id=str).and_a(name=str).and_a(color=Color)

from __future__ import annotations

import random
from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, Type

from fastapi import FastAPI

from apexdevkit.fastapi import FastApiBuilder
from apexdevkit.fastapi.builder import RestfulServiceBuilder
from apexdevkit.fastapi.router import RestfulRouter
from apexdevkit.testing import RestfulName
from apexdevkit.testing.fake import FakeResource
from tests.resource.sample_api import Apple, AppleFields, Color, Name, PriceFields


def setup(infra: RestfulServiceBuilder) -> FastAPI:
    return (
        FastApiBuilder()
        .with_title("Apple API")
        .with_version("1.0.0")
        .with_description("Sample API for unit testing various testing routines")
        .with_route(
            apples=RestfulRouter()
            .with_name(RestfulName("apple"))
            .with_fields(AppleFields())
            .with_infra(infra)
            .with_sub_resource(
                prices=(
                    RestfulRouter()
                    .with_name(RestfulName("price"))
                    .with_fields(PriceFields())
                    .with_infra(infra)
                    .with_parent("apple")
                    .with_delete_one_endpoint()
                    .build()
                )
            )
            .default()
            .with_replace_one_endpoint()
            .with_replace_many_endpoint()
            .build()
        )
        .build()
    )


@dataclass
class FakeApple(FakeResource[Apple]):
    id: str | None = None
    name: Name | None = None
    item_type: Type[Apple] = field(default=Apple)

    @cached_property
    def _raw(self) -> dict[str, Any]:
        return {
            "id": self.id or self.fake.uuid(),
            "name": self._name(),
            "color": random.choice(list(Color)).value,
        }

    def _name(self) -> dict[str, Any]:
        name = self.name or Name(self.fake.text(length=10), self.fake.text(length=10))
        return {"scientific": name.scientific, "common": name.common}

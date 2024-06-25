from fastapi import FastAPI

from apexdevkit.fastapi import FastApiBuilder
from apexdevkit.fastapi.router import RestfulRouter
from apexdevkit.testing import RestfulName
from tests.sample_api import AppleFields, FakeServiceBuilder, PriceFields


def setup(infra: FakeServiceBuilder) -> FastAPI:
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
                    .with_parent("apple")
                    .with_infra(infra)
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

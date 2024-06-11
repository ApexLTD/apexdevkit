from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from apexdevkit.fastapi import FastApiBuilder
from apexdevkit.fastapi.router import RestfulRouter, RestfulServiceBuilder
from apexdevkit.fastapi.service import RestfulRepository, RestfulService
from apexdevkit.repository import InMemoryRepository
from apexdevkit.testing import RestCollection, RestfulName, RestResource
from tests.sample_api import Apple, AppleFields


@pytest.fixture
def infra() -> SampleServiceBuilder:
    return SampleServiceBuilder()


@pytest.fixture
def fake_user() -> FakeUser:
    return FakeUser()


@pytest.fixture
def http(infra: SampleServiceBuilder, fake_user: FakeUser) -> TestClient:
    return TestClient(setup(infra, fake_user))


@pytest.fixture
def resource(http: TestClient) -> RestResource:
    return RestCollection(http, RestfulName("apple"))


@dataclass
class FakeUser:
    times_called: int = 0

    def user(self) -> str:
        self.times_called += 1
        return "user"


@dataclass
class SampleServiceBuilder(RestfulServiceBuilder):
    times_called: int = 0

    def with_user(self, user: Any) -> "RestfulServiceBuilder":
        self.times_called += 1
        self.user = user
        return super().with_user(user)

    def build(self) -> RestfulService:
        return RestfulRepository(Apple, InMemoryRepository[Apple].for_dataclass(Apple))


def setup(infra: SampleServiceBuilder, fake_user: FakeUser) -> FastAPI:
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
            .with_create_one_endpoint(extract_user=fake_user.user)
            .with_create_many_endpoint(extract_user=fake_user.user)
            .with_read_one_endpoint(extract_user=fake_user.user)
            .with_read_all_endpoint(extract_user=fake_user.user)
            .with_update_one_endpoint(extract_user=fake_user.user)
            .with_update_many_endpoint(extract_user=fake_user.user)
            .with_delete_one_endpoint(extract_user=fake_user.user)
            .build()
        )
        .build()
    )

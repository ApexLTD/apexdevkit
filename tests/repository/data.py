from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from faker import Faker

from apexdevkit.repository import Entity
from apexdevkit.testing.fake import Fake


@dataclass(frozen=True, kw_only=True)
class AppleItem(Entity):
    color: str


@dataclass(frozen=True, kw_only=True)
class CompanyInMemoryItem(Entity):
    name: str
    code: str
    address: AddressInMemoryItem

    @classmethod
    def fake(cls, **kwargs: Any) -> CompanyInMemoryItem:
        faker = Faker()

        return cls(
            id=kwargs.get("id") or Fake().uuid(),
            name=kwargs.get("name") or faker.company(),
            code=kwargs.get("code") or faker.ein(),
            address=kwargs.get("address") or AddressInMemoryItem.fake(),
        )


@dataclass(frozen=True)
class AddressInMemoryItem:
    street: str
    city: str
    state: str
    country: str
    zip: str

    @classmethod
    def fake(cls) -> AddressInMemoryItem:
        faker = Faker()

        return cls(
            faker.street_name(),
            faker.city(),
            faker.state(),
            faker.country(),
            faker.zipcode(),
        )


@dataclass(frozen=True, kw_only=True)
class SqliteTableItem(Entity):
    name: str
    count: int

    parent: int | None = None

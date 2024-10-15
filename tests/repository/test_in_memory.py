from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from faker import Faker

from apexdevkit.error import DoesNotExistError, ExistsError
from apexdevkit.repository.in_memory import AttributeKey, InMemoryRepository
from apexdevkit.testing.fake import Fake


@dataclass
class _Company:
    id: str
    name: str
    code: str
    address: _Address

    @classmethod
    def fake(cls, **kwargs: Any) -> _Company:
        faker = Faker()

        return cls(
            id=kwargs.get("id") or Fake().uuid(),
            name=kwargs.get("name") or faker.company(),
            code=kwargs.get("code") or faker.ein(),
            address=kwargs.get("address") or _Address.fake(),
        )


@dataclass
class _Address:
    street: str
    city: str
    state: str
    country: str
    zip: str

    @classmethod
    def fake(cls) -> _Address:
        faker = Faker()

        return cls(
            faker.street_name(),
            faker.city(),
            faker.state(),
            faker.country(),
            faker.zipcode(),
        )


def test_should_not_read_unknown() -> None:
    unknown_id = Fake().uuid()

    repository = InMemoryRepository().build()

    with pytest.raises(DoesNotExistError):
        repository.read(unknown_id)


def test_should_persist() -> None:
    company = _Company.fake()
    repository = InMemoryRepository().build()

    repository.create(company)

    assert repository.read(company.id) == company


def test_should_read_by_custom_field() -> None:
    company = _Company.fake()
    repository = (
        InMemoryRepository()
        .with_key(AttributeKey("id"))
        .with_key(AttributeKey("code"))
        .build()
    )

    repository.create(company)

    assert repository.read(company.code) == company


def test_should_not_duplicate() -> None:
    company = _Company.fake()
    repository = (
        InMemoryRepository()
        .with_key(function=lambda item: f"code<{item.code}>")
        .and_seeded(company)
        .build()
    )

    duplicate = _Company.fake(code=company.code)
    with pytest.raises(ExistsError) as cm:
        repository.create(duplicate)

    assert cm.value.id == company.id
    assert str(cm.value) == f"code<{company.code}>"


def test_should_not_not_duplicate_many_fields() -> None:
    company = _Company.fake()
    repository = (
        InMemoryRepository()
        .with_key(function=lambda item: f"code<{item.code}>")
        .and_key(function=lambda item: f"name<{item.name}>")
        .and_seeded(company)
        .build()
    )

    duplicate = _Company.fake(name=company.name, code=company.code)
    with pytest.raises(ExistsError) as cm:
        repository.create(duplicate)

    assert cm.value.id == company.id
    assert str(cm.value) == f"code<{company.code}>,name<{company.name}>"


def test_should_list() -> None:
    companies = [_Company.fake() for _ in range(10)]
    repository = InMemoryRepository().with_seeded(*companies).build()

    assert len(repository) == len(companies)
    assert list(repository) == companies


def test_should_update() -> None:
    company = _Company.fake()
    repository = InMemoryRepository().with_seeded(company).build()

    updated = _Company.fake(id=company.id)
    repository.update(updated)

    assert repository.read(company.id) == updated


def test_should_not_delete_unknown() -> None:
    unknown_id = Fake().uuid()

    with pytest.raises(DoesNotExistError):
        InMemoryRepository().build().delete(unknown_id)


def test_should_delete() -> None:
    company = _Company.fake()
    repository = InMemoryRepository().with_seeded(company).build()

    repository.delete(company.id)

    with pytest.raises(DoesNotExistError):
        repository.read(company.id)

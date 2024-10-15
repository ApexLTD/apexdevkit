from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from faker import Faker

from apexdevkit.error import DoesNotExistError, ExistsError
from apexdevkit.repository import ManyKeyRepository
from apexdevkit.repository.in_memory import AttributeKey, InMemoryKeyValueStore
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


_Repository = ManyKeyRepository[_Company]


@pytest.fixture
def repository() -> _Repository:
    return ManyKeyRepository[_Company](InMemoryKeyValueStore())


def test_should_not_read_unknown(repository: _Repository) -> None:
    unknown_id = Fake().uuid()

    with pytest.raises(DoesNotExistError):
        repository.read(unknown_id)


def test_should_persist(repository: _Repository) -> None:
    company = _Company.fake()
    repository = repository.with_key(AttributeKey("id"))

    repository.create(company)

    persisted = repository.read(company.id)
    assert persisted == company


def test_should_read_by_custom_field(repository: _Repository) -> None:
    company = _Company.fake()
    repository = repository.with_key(AttributeKey("id")).with_key(AttributeKey("code"))

    repository.create(company)

    persisted = repository.read(company.code)
    assert persisted == company


def test_should_not_duplicate(repository: _Repository) -> None:
    company = _Company.fake()
    repository = repository.with_key(
        function=lambda item: f"code<{item.code}>"
    ).with_seeded(company)

    duplicate = _Company.fake(code=company.code)
    with pytest.raises(ExistsError) as cm:
        repository.create(duplicate)

    assert cm.value.id == company.id
    assert str(cm.value) == f"code<{company.code}>"


def test_should_not_not_duplicate_many_fields(repository: _Repository) -> None:
    company = _Company.fake()
    repository = (
        repository.with_key(function=lambda item: f"code<{item.code}>")
        .with_key(function=lambda item: f"name<{item.name}>")
        .with_seeded(company)
    )

    duplicate = _Company.fake(name=company.name, code=company.code)
    with pytest.raises(ExistsError) as cm:
        repository.create(duplicate)

    assert cm.value.id == company.id
    assert str(cm.value) == f"code<{company.code}>,name<{company.name}>"


def test_should_list(repository: _Repository) -> None:
    companies = [_Company.fake() for _ in range(10)]

    repository = repository.with_key(AttributeKey("id")).with_seeded(*companies)

    assert len(repository) == len(companies)
    assert list(repository) == companies


def test_should_update(repository: _Repository, faker: Faker) -> None:
    company = _Company.fake()
    repository = repository.with_key(AttributeKey("id")).with_seeded(company)

    updated = _Company.fake(id=company.id)
    repository.update(updated)

    persisted = repository.read(company.id)
    assert persisted == updated


def test_should_not_delete_unknown(repository: _Repository) -> None:
    unknown_id = Fake().uuid()

    with pytest.raises(DoesNotExistError):
        repository.delete(unknown_id)


def test_should_delete(repository: _Repository) -> None:
    company = _Company.fake()
    repository = repository.with_key(AttributeKey("id")).with_seeded(company)

    repository.delete(company.id)

    with pytest.raises(DoesNotExistError):
        repository.read(company.id)

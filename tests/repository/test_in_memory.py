from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

import pytest
from faker import Faker

from apexdevkit.error import DoesNotExistError, ExistsError
from apexdevkit.formatter import DataclassFormatter
from apexdevkit.repository import InMemoryRepository
from apexdevkit.repository.in_memory import AttributeKey
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


_Repository = InMemoryRepository[_Company]


@pytest.fixture
def repository() -> _Repository:
    return InMemoryRepository[_Company](
        formatter=DataclassFormatter[_Company](_Company).with_nested(
            address=DataclassFormatter[_Address](_Address)
        )
    )


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


def test_should_preserve_object(repository: _Repository) -> None:
    company = _Company.fake(address=_Address.fake())
    preserved = replace(company, address=replace(company.address))
    repository = repository.with_key(AttributeKey("id")).with_seeded(company)
    company.name = "changed"
    company.address.city = "changed"

    assert repository.read(company.id) == preserved


def test_should_search(repository: _Repository) -> None:
    company = _Company.fake()

    repository = repository.with_key(AttributeKey("id")).with_seeded(company)

    assert list(repository.search(name=company.name)) == [company]


def test_should_search_unique(repository: _Repository, faker: Faker) -> None:
    company_1 = _Company.fake()
    company_2 = _Company.fake()
    repository = repository.with_key(AttributeKey("id")).with_seeded(
        company_1, company_2
    )

    assert list(repository.search(name=company_2.name)) == [company_2]


def test_should_search_many(repository: _Repository) -> None:
    company_1 = _Company.fake()
    company_2 = _Company.fake(name=company_1.name)
    company_3 = _Company.fake()
    repository = repository.with_key(AttributeKey("id")).with_seeded(
        company_1, company_2, company_3
    )

    searched = repository.search(name=company_1.name)

    assert len(list(searched)) == 2
    assert all(company in [company_1, company_2] for company in searched)


def test_should_search_with_multiple_kwargs(repository: _Repository) -> None:
    company_1 = _Company.fake()
    company_2 = _Company.fake(name=company_1.name)
    company_3 = _Company.fake()
    repository = repository.with_key(AttributeKey("id")).with_seeded(
        company_1, company_2, company_3
    )

    searched = repository.search(name=company_1.name, code=company_1.code)

    assert list(searched) == [company_1]

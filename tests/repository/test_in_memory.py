from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

import pytest
from faker import Faker

from apexdevkit.error import DoesNotExistError, ExistsError
from apexdevkit.formatter import DataclassFormatter
from apexdevkit.repository import InMemoryRepository
from apexdevkit.repository.in_memory import AttributeKey


@dataclass
class _Company:
    id: UUID
    name: str
    code: str


@dataclass
class _InnerClass:
    id: UUID
    company: _Company


@dataclass
class _OuterClass:
    id: UUID
    inner: _InnerClass


def test_should_not_read_unknown() -> None:
    unknown_id = uuid4()
    repository = InMemoryRepository[UUID, _Company](
        formatter=DataclassFormatter[_Company](_Company)
    )

    with pytest.raises(DoesNotExistError):
        repository.read(unknown_id)


def test_should_persist(faker: Faker) -> None:
    company = _Company(id=uuid4(), name=faker.company(), code=faker.ein())
    repository = InMemoryRepository[UUID, _Company](
        formatter=DataclassFormatter[_Company](_Company)
    ).with_key(AttributeKey("id"))

    repository.create(company)

    persisted = repository.read(company.id)
    assert persisted == company


def test_should_persist_seeded(faker: Faker) -> None:
    company_1 = _Company(id=uuid4(), name=faker.company(), code=faker.ein())
    company_2 = _Company(id=uuid4(), name=faker.company(), code=faker.ein())

    repository = (
        InMemoryRepository[UUID, _Company](
            formatter=DataclassFormatter[_Company](_Company)
        )
        .with_key(AttributeKey("id"))
        .with_seeded(company_1, company_2)
    )

    persisted_1 = repository.read(company_1.id)
    assert persisted_1 == company_1
    persisted_2 = repository.read(company_2.id)
    assert persisted_2 == company_2


def test_should_read_by_custom_field(faker: Faker) -> None:
    company = _Company(id=uuid4(), name=faker.company(), code=faker.ein())
    repository = (
        InMemoryRepository[UUID | str, _Company](
            formatter=DataclassFormatter[_Company](_Company)
        )
        .with_key(AttributeKey("id"))
        .with_key(AttributeKey("code"))
    )

    repository.create(company)

    persisted = repository.read(company.code)
    assert persisted == company


def test_should_not_duplicate(faker: Faker) -> None:
    company = _Company(id=uuid4(), name=faker.company(), code=faker.ein())
    repository = InMemoryRepository[UUID, _Company](
        formatter=DataclassFormatter[_Company](_Company)
    ).with_key(function=lambda item: f"code<{item.code}>")
    repository.create(company)

    duplicate = _Company(id=uuid4(), name=faker.company(), code=company.code)
    with pytest.raises(ExistsError) as cm:
        repository.create(duplicate)

    assert cm.value.id == company.id
    assert str(cm.value) == f"code<{company.code}>"


def test_should_not_not_duplicate_many_fields(faker: Faker) -> None:
    company = _Company(id=uuid4(), name=faker.company(), code=faker.ein())
    repository = (
        InMemoryRepository[UUID, _Company](
            formatter=DataclassFormatter[_Company](_Company)
        )
        .with_key(function=lambda item: f"code<{item.code}>")
        .with_key(function=lambda item: f"name<{item.name}>")
    )
    repository.create(company)

    duplicate = _Company(id=uuid4(), name=company.name, code=company.code)
    with pytest.raises(ExistsError) as cm:
        repository.create(duplicate)

    assert cm.value.id == company.id
    assert str(cm.value) == f"code<{company.code}>,name<{company.name}>"


def test_should_list(faker: Faker) -> None:
    companies = [
        _Company(id=uuid4(), name=faker.company(), code=faker.ein()),
        _Company(id=uuid4(), name=faker.company(), code=faker.ein()),
    ]

    repository = InMemoryRepository[UUID, _Company](
        formatter=DataclassFormatter[_Company](_Company)
    ).with_key(AttributeKey("id"))
    for company in companies:
        repository.create(company)

    assert len(repository) == 2
    assert list(repository) == companies


def test_should_update(faker: Faker) -> None:
    company = _Company(id=uuid4(), name=faker.company(), code=faker.ein())
    repository = InMemoryRepository[UUID, _Company](
        formatter=DataclassFormatter[_Company](_Company)
    ).with_key(AttributeKey("id"))
    repository.create(company)

    updated = _Company(id=company.id, name=faker.company(), code=faker.ein())
    repository.update(updated)

    persisted = repository.read(company.id)
    assert persisted == updated


def test_should_update_many(faker: Faker) -> None:
    company_1 = _Company(id=uuid4(), name=faker.company(), code=faker.ein())
    company_2 = _Company(id=uuid4(), name=faker.company(), code=faker.ein())
    repository = InMemoryRepository[UUID, _Company](
        formatter=DataclassFormatter[_Company](_Company)
    ).with_key(AttributeKey("id"))
    repository.create_many([company_1, company_2])

    updated_1 = _Company(id=company_1.id, name=faker.company(), code=faker.ein())
    updated_2 = _Company(id=company_2.id, name=faker.company(), code=faker.ein())
    repository.update_many([updated_1, updated_2])

    persisted_1 = repository.read(company_1.id)
    persisted_2 = repository.read(company_2.id)
    assert persisted_1 == updated_1
    assert persisted_2 == updated_2


def test_should_not_delete_unknown() -> None:
    unknown_id = uuid4()
    repository = InMemoryRepository[UUID, _Company](
        formatter=DataclassFormatter[_Company](_Company)
    )

    with pytest.raises(DoesNotExistError):
        repository.delete(unknown_id)


def test_should_delete(faker: Faker) -> None:
    company = _Company(id=uuid4(), name=faker.company(), code=faker.ein())
    repository = InMemoryRepository[UUID, _Company](
        formatter=DataclassFormatter[_Company](_Company)
    ).with_key(AttributeKey("id"))
    repository.create(company)

    repository.delete(company.id)

    with pytest.raises(DoesNotExistError):
        repository.read(company.id)


def test_should_preserve_object() -> None:
    _id = uuid4()
    company = _Company(id=_id, name="company", code="code")
    repository = InMemoryRepository[UUID, _Company](
        formatter=DataclassFormatter[_Company](_Company)
    ).with_key(AttributeKey("id"))
    repository.create(company)
    company.name = "changed"

    assert repository.read(company.id) == _Company(id=_id, name="company", code="code")


def test_should_preserve_nested_object() -> None:
    _id = uuid4()
    company = _Company(id=_id, name="company", code="code")
    inner = _InnerClass(id=_id, company=company)
    outer = _OuterClass(id=_id, inner=inner)
    f = DataclassFormatter[_OuterClass](_OuterClass).with_nested(
        inner=DataclassFormatter[_InnerClass](_InnerClass).with_nested(
            company=DataclassFormatter[_Company](_Company)
        )
    )
    repository = InMemoryRepository[UUID, _OuterClass](formatter=f).with_key(
        AttributeKey("id")
    )
    repository.create(outer)
    company.name = "changed"

    assert repository.read(_id) == repository.read(_id)


def test_should_search(faker: Faker) -> None:
    company = _Company(id=uuid4(), name=faker.company(), code=faker.ein())
    repository = InMemoryRepository[UUID, _Company](
        formatter=DataclassFormatter[_Company](_Company)
    ).with_key(AttributeKey("id"))

    repository.create(company)

    assert list(repository.search(name=company.name)) == [company]


def test_should_search_unique(faker: Faker) -> None:
    company_1 = _Company(id=uuid4(), name=faker.company(), code=faker.ein())
    company_2 = _Company(id=uuid4(), name=faker.company(), code=faker.ein())
    repository = InMemoryRepository[UUID, _Company](
        formatter=DataclassFormatter[_Company](_Company)
    ).with_key(AttributeKey("id"))

    repository.create(company_1)
    repository.create(company_2)

    assert list(repository.search(name=company_2.name)) == [company_2]


def test_should_search_many(faker: Faker) -> None:
    company_1 = _Company(id=uuid4(), name=faker.company(), code=faker.ein())
    company_2 = _Company(id=uuid4(), name=company_1.name, code=faker.ein())
    company_3 = _Company(id=uuid4(), name=faker.company(), code=faker.ein())

    repository = InMemoryRepository[UUID, _Company](
        formatter=DataclassFormatter[_Company](_Company)
    ).with_key(AttributeKey("id"))

    repository.create(company_1)
    repository.create(company_2)
    repository.create(company_3)

    searched = repository.search(name=company_1.name)

    assert len(list(searched)) == 2
    assert all(company in [company_1, company_2] for company in searched)


def test_should_search_with_multiple_kwargs(faker: Faker) -> None:
    company_1 = _Company(id=uuid4(), name=faker.company(), code=faker.ein())
    company_2 = _Company(id=uuid4(), name=company_1.name, code=faker.ein())
    company_3 = _Company(id=uuid4(), name=faker.company(), code=faker.ein())

    repository = InMemoryRepository[UUID, _Company](
        formatter=DataclassFormatter[_Company](_Company)
    ).with_key(AttributeKey("id"))

    repository.create(company_1)
    repository.create(company_2)
    repository.create(company_3)

    searched = repository.search(name=company_1.name, code=company_1.code)

    assert len(list(searched)) == 1
    assert list(searched) == [company_1]

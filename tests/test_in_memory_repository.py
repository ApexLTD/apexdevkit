from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any
from uuid import UUID, uuid4

import pytest
from faker import Faker

from pydevtools.error import DoesNotExistError, ExistsError
from pydevtools.repository import InMemoryRepository


@dataclass
class _Company:
    id: UUID
    name: str
    code: str


@dataclass(frozen=True)
class _Formatter:
    def load(self, raw: dict[str, Any]) -> _Company:
        return _Company(**raw)

    def dump(self, item: _Company) -> dict[str, Any]:
        return asdict(item)


@dataclass
class _InnerClass:
    id: UUID
    company: _Company


@dataclass(frozen=True)
class _InnerFormatter:
    def load(self, raw: dict[str, Any]) -> _InnerClass:
        return _InnerClass(company=_Formatter().load(raw.pop("company")), **raw)

    def dump(self, item: _InnerClass) -> dict[str, Any]:
        return asdict(item)


@dataclass
class _OuterClass:
    id: UUID
    inner: _InnerClass


@dataclass(frozen=True)
class _OuterFormatter:
    def load(self, raw: dict[str, Any]) -> _OuterClass:
        return _OuterClass(inner=_InnerFormatter().load(raw.pop("inner")), **raw)

    def dump(self, item: _OuterClass) -> dict[str, Any]:
        return asdict(item)


def test_should_not_read_unknown() -> None:
    unknown_id = uuid4()
    repository = InMemoryRepository[_Company](formatter=_Formatter())

    with pytest.raises(DoesNotExistError):
        repository.read(unknown_id)


def test_should_persist(faker: Faker) -> None:
    company = _Company(id=uuid4(), name=faker.company(), code=faker.ein())
    repository = InMemoryRepository[_Company](formatter=_Formatter())

    repository.create(company)

    persisted = repository.read(company.id)
    assert persisted == company


def test_should_persist_seeded(faker: Faker) -> None:
    company_1 = _Company(id=uuid4(), name=faker.company(), code=faker.ein())
    company_2 = _Company(id=uuid4(), name=faker.company(), code=faker.ein())

    repository = InMemoryRepository[_Company](formatter=_Formatter()).with_seeded(
        company_1, company_2
    )

    persisted_1 = repository.read(company_1.id)
    assert persisted_1 == company_1
    persisted_2 = repository.read(company_2.id)
    assert persisted_2 == company_2


def test_should_read_by_custom_field(faker: Faker) -> None:
    company = _Company(id=uuid4(), name=faker.company(), code=faker.ein())
    repository = InMemoryRepository[_Company](formatter=_Formatter()).with_searchable(
        "code"
    )

    repository.create(company)

    persisted = repository.read(company.code)
    assert persisted == company


def test_should_not_duplicate(faker: Faker) -> None:
    company = _Company(id=uuid4(), name=faker.company(), code=faker.ein())
    repository = InMemoryRepository[_Company](formatter=_Formatter()).with_unique(
        criteria=lambda item: f"code<{item.code}>"
    )
    repository.create(company)

    duplicate = _Company(id=uuid4(), name=faker.company(), code=company.code)
    with pytest.raises(ExistsError) as cm:
        repository.create(duplicate)

    assert cm.value.id == company.id
    assert str(cm.value) == f"code<{company.code}>"


def test_should_not_not_duplicate_many_fields(faker: Faker) -> None:
    company = _Company(id=uuid4(), name=faker.company(), code=faker.ein())
    repository = (
        InMemoryRepository[_Company](formatter=_Formatter())
        .with_unique(criteria=lambda item: f"code<{item.code}>")
        .with_unique(criteria=lambda item: f"name<{item.name}>")
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

    repository = InMemoryRepository[_Company](formatter=_Formatter())
    for company in companies:
        repository.create(company)

    assert len(repository) == 2
    assert list(repository) == companies


def test_should_update(faker: Faker) -> None:
    company = _Company(id=uuid4(), name=faker.company(), code=faker.ein())
    repository = InMemoryRepository[_Company](formatter=_Formatter())
    repository.create(company)

    updated = _Company(id=company.id, name=faker.company(), code=faker.ein())
    repository.update(updated)

    persisted = repository.read(company.id)
    assert persisted == updated


def test_should_update_many(faker: Faker) -> None:
    company_1 = _Company(id=uuid4(), name=faker.company(), code=faker.ein())
    company_2 = _Company(id=uuid4(), name=faker.company(), code=faker.ein())
    repository = InMemoryRepository[_Company](formatter=_Formatter())
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
    repository = InMemoryRepository[_Company](formatter=_Formatter())

    with pytest.raises(DoesNotExistError):
        repository.delete(unknown_id)


def test_should_delete(faker: Faker) -> None:
    company = _Company(id=uuid4(), name=faker.company(), code=faker.ein())
    repository = InMemoryRepository[_Company](formatter=_Formatter())
    repository.create(company)

    repository.delete(company.id)

    with pytest.raises(DoesNotExistError):
        repository.read(company.id)


def test_should_preserve_object() -> None:
    _id = uuid4()
    company = _Company(id=_id, name="company", code="code")
    repository = InMemoryRepository[_Company](formatter=_Formatter())
    repository.create(company)
    company.name = "changed"

    assert repository.read(company.id) == _Company(id=_id, name="company", code="code")


def test_should_preserve_nested_object() -> None:
    _id = uuid4()
    company = _Company(id=_id, name="company", code="code")
    inner = _InnerClass(id=_id, company=company)
    outer = _OuterClass(id=_id, inner=inner)
    repository = InMemoryRepository[_OuterClass](formatter=_OuterFormatter())
    repository.create(outer)
    company.name = "changed"

    assert repository.read(_id) == repository.read(_id)

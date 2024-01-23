from dataclasses import dataclass
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


def test_should_not_read_unknown() -> None:
    unknown_id = uuid4()
    repository = InMemoryRepository[_Company]()

    with pytest.raises(DoesNotExistError):
        repository.read(unknown_id)


def test_should_persist(faker: Faker) -> None:
    partner = _Company(id=uuid4(), name=faker.company(), code=faker.ein())
    repository = InMemoryRepository[_Company]()

    repository.create(partner)

    persisted = repository.read(partner.id)
    assert persisted == partner


def test_should_read_by_custom_field(faker: Faker) -> None:
    partner = _Company(id=uuid4(), name=faker.company(), code=faker.ein())
    repository = InMemoryRepository[_Company]().with_searchable("code")

    repository.create(partner)

    persisted = repository.read(partner.code)
    assert persisted == partner


def test_should_not_duplicate(faker: Faker) -> None:
    company = _Company(id=uuid4(), name=faker.company(), code=faker.ein())
    repository = InMemoryRepository[_Company]().with_unique(
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
        InMemoryRepository[_Company]()
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

    repository = InMemoryRepository[_Company]()
    for company in companies:
        repository.create(company)

    assert len(repository) == 2
    assert list(repository) == companies


def test_should_update(faker: Faker) -> None:
    company = _Company(id=uuid4(), name=faker.company(), code=faker.ein())
    repository = InMemoryRepository[_Company]()
    repository.create(company)

    updated = _Company(id=company.id, name=faker.company(), code=faker.ein())
    repository.update(updated)

    persisted = repository.read(company.id)
    assert persisted == updated


def test_should_delete(faker: Faker) -> None:
    company = _Company(id=uuid4(), name=faker.company(), code=faker.ein())
    repository = InMemoryRepository[_Company]()
    repository.create(company)

    repository.delete(company.id)

    with pytest.raises(DoesNotExistError):
        repository.read(company.id)

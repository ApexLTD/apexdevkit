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

    def __eq__(self, other: object) -> bool:
        assert isinstance(other, _Company), f"Cannot compare to {type(other)}"

        return self.code == other.code


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


def test_should_not_duplicate_id(faker: Faker) -> None:
    company = _Company(id=uuid4(), name=faker.company(), code=faker.ein())
    repository = InMemoryRepository[_Company]()
    repository.create(company)

    with pytest.raises(ExistsError) as cm:
        repository.create(company)

    assert cm.value.id == company.id


def test_should_not_duplicate_unique_field(faker: Faker) -> None:
    company = _Company(id=uuid4(), name=faker.company(), code=faker.ein())
    repository = InMemoryRepository[_Company]()
    repository.create(company)

    duplicate = _Company(id=uuid4(), name=faker.company(), code=company.code)
    with pytest.raises(ExistsError) as cm:
        repository.create(duplicate)

    assert cm.value.id == company.id


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

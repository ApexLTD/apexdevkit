import pytest

from apexdevkit.error import DoesNotExistError, ExistsError
from apexdevkit.key_fn import AttributeKey
from apexdevkit.repository.in_memory import InMemoryRepository
from apexdevkit.testing.fake import Fake
from tests.repository.data import CompanyInMemoryItem


def test_should_not_read_unknown() -> None:
    unknown_id = Fake().uuid()

    repository = InMemoryRepository[CompanyInMemoryItem]()

    with pytest.raises(DoesNotExistError):
        repository.read(unknown_id)


def test_should_persist() -> None:
    company = CompanyInMemoryItem.fake()
    repository = InMemoryRepository[CompanyInMemoryItem]()

    repository.create(company)

    assert repository.read(company.id) == company


def test_should_read_by_custom_field() -> None:
    company = CompanyInMemoryItem.fake()
    repository = InMemoryRepository[CompanyInMemoryItem]().with_key(
        AttributeKey("code")
    )

    repository.create(company)

    assert repository.read(company.code) == company


def test_should_not_duplicate() -> None:
    company = CompanyInMemoryItem.fake()
    repository = (
        InMemoryRepository[CompanyInMemoryItem]()
        .with_key(function=lambda item: f"code<{item.code}>")
        .and_seeded(company)
    )

    duplicate = CompanyInMemoryItem.fake(code=company.code)
    with pytest.raises(ExistsError) as cm:
        repository.create(duplicate)

    assert cm.value.id == company.id
    assert str(cm.value) == f"code<{company.code}>"


@pytest.mark.skip(reason="Removed intentionally")
def test_should_not_not_duplicate_many_fields() -> None:
    company = CompanyInMemoryItem.fake()
    repository = (
        InMemoryRepository[CompanyInMemoryItem]()
        .with_key(function=lambda item: f"code<{item.code}>")
        .and_key(function=lambda item: f"name<{item.name}>")
        .and_seeded(company)
    )

    duplicate = CompanyInMemoryItem.fake(name=company.name, code=company.code)
    with pytest.raises(ExistsError) as cm:
        repository.create(duplicate)

    assert cm.value.id == company.id
    assert str(cm.value) == f"code<{company.code}>,name<{company.name}>"


def test_should_list() -> None:
    companies = [CompanyInMemoryItem.fake() for _ in range(10)]
    repository = InMemoryRepository[CompanyInMemoryItem]().and_seeded(*companies)

    assert len(repository) == len(companies)
    assert all(company in companies for company in repository)


def test_should_update() -> None:
    company = CompanyInMemoryItem.fake()
    repository = InMemoryRepository[CompanyInMemoryItem]().with_seeded(company)

    updated = CompanyInMemoryItem.fake(id=company.id)
    repository.update(updated)

    assert repository.read(company.id) == updated


def test_should_not_delete_unknown() -> None:
    unknown_id = Fake().uuid()

    with pytest.raises(DoesNotExistError):
        InMemoryRepository[CompanyInMemoryItem]().delete(unknown_id)


def test_should_delete() -> None:
    company = CompanyInMemoryItem.fake()
    repository = InMemoryRepository[CompanyInMemoryItem]().with_seeded(company)

    repository.delete(company.id)

    with pytest.raises(DoesNotExistError):
        repository.read(company.id)

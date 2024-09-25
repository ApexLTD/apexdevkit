from dataclasses import dataclass, replace

import pytest
from _pytest.fixtures import fixture
from faker.generator import random

from apexdevkit.error import DoesNotExistError, ExistsError
from apexdevkit.formatter import DataclassFormatter
from apexdevkit.repository.alternative import FormatterRepository, MemoryRepositoryBase
from apexdevkit.testing.fake import Fake


@dataclass
class Person:
    id: str
    name: str


@fixture
def repository() -> FormatterRepository[Person]:
    return FormatterRepository(
        base=MemoryRepositoryBase(),
        formatter=DataclassFormatter[Person](Person),
    )


def fake_person() -> Person:
    return Person(
        Fake().uuid(),
        Fake().last_name(),
    )


def test_should_create(repository: FormatterRepository[Person]) -> None:
    fake = fake_person()
    repository.create(fake)

    assert repository.read(fake.id) == fake


def test_should_create_many(repository: FormatterRepository[Person]) -> None:
    fakes = [fake_person() for _ in range(10)]
    repository.create_many(fakes)

    for fake in fakes:
        assert repository.read(fake.id) == fake


def test_should_read_many(repository: FormatterRepository[Person]) -> None:
    fakes = [fake_person() for _ in range(10)]
    repository.create_many(fakes)

    assert fakes == list(repository)


def test_should_update(repository: FormatterRepository[Person]) -> None:
    fake = fake_person()
    repository.create(fake)

    fake = replace(fake, name="updated")

    repository.update(fake)

    assert fake == repository.read(fake.id)


def test_should_update_many(repository: FormatterRepository[Person]) -> None:
    fakes = [fake_person() for _ in range(10)]
    repository.create_many(fakes)

    updated_fakes = []
    for i, fake in enumerate(fakes):
        updated_fakes.append(replace(fake, name=f"updated_{i}"))

    repository.update_many(updated_fakes)

    assert updated_fakes == list(repository)


def test_should_delete(repository: FormatterRepository[Person]) -> None:
    fake = fake_person()
    repository.create(fake)

    repository.delete(fake.id)

    with pytest.raises(DoesNotExistError):
        repository.read(fake.id)


def test_correct_length(repository: FormatterRepository[Person]) -> None:
    random_length = random.randint(1, 10)
    fakes = [fake_person() for _ in range(random_length)]

    repository.create_many(fakes)

    assert random_length == len(repository)


def test_should_not_create_duplicate(repository: FormatterRepository[Person]) -> None:
    fake = fake_person()

    repository.create(fake)

    with pytest.raises(ExistsError):
        repository.create(fake)


def test_should_not_create_many_duplicates(
    repository: FormatterRepository[Person],
) -> None:
    fakes = [fake_person() for _ in range(10)]

    repository.create_many(fakes)

    with pytest.raises(ExistsError):
        repository.create_many(fakes)


def test_should_not_update_nonexistent(repository: FormatterRepository[Person]) -> None:
    fake = fake_person()

    with pytest.raises(DoesNotExistError):
        repository.update(fake)


def test_should_not_update_many_nonexistent(
    repository: FormatterRepository[Person],
) -> None:
    fakes = [fake_person() for _ in range(10)]

    with pytest.raises(DoesNotExistError):
        repository.update_many(fakes)


def test_should_not_delete_nonexistent(repository: FormatterRepository[Person]) -> None:
    fake = fake_person()

    with pytest.raises(DoesNotExistError):
        repository.delete(fake.id)

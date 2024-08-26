import dataclasses
from dataclasses import dataclass, field
from typing import Any, Iterator
from uuid import uuid4

import pytest

from apexdevkit.error import DoesNotExistError, ExistsError
from apexdevkit.repository.connector import MongoDBConnector
from apexdevkit.repository.database import MongoDatabase
from apexdevkit.repository.mongo import MongoDBRepository, MongoTable


@dataclass
class _Item:
    external_id: str

    id: str = field(default_factory=lambda: str(uuid4()))


class FakeTable(MongoTable[_Item]):
    def to_dict(self, item: _Item) -> dict[str, Any]:
        return dataclasses.asdict(item)

    def load(self, data: dict[str, Any]) -> _Item:
        data.pop("_id")
        return _Item(**data)

    def get_id(self, item: _Item) -> str:
        return item.id


@pytest.fixture
def repository() -> Iterator[MongoDBRepository[_Item]]:
    repo = MongoDBRepository(
        MongoDatabase(
            MongoDBConnector("mongodb://10.10.0.77:2717/"),
            "test_database",
            "test_collection",
        ),
        FakeTable(),
    )
    try:
        yield repo
    finally:
        repo.delete_all()


def test_should_list_nothing_when_empty(repository: MongoDBRepository[_Item]) -> None:
    assert len(repository) == 0
    assert list(repository) == []


def test_should_not_read_unknown(repository: MongoDBRepository[_Item]) -> None:
    with pytest.raises(DoesNotExistError):
        repository.read(str(uuid4()))


def test_should_create(repository: MongoDBRepository[_Item]) -> None:
    item = _Item(id=str(uuid4()), external_id=str(uuid4()))
    assert repository.create(item) == item


def test_should_not_duplicate_on_create(repository: MongoDBRepository[_Item]) -> None:
    item = _Item(id=str(uuid4()), external_id=str(uuid4()))
    repository.create(item)
    with pytest.raises(ExistsError, match=f"_Item with id<{item.id}> already exists."):
        repository.create(item)


def test_should_create_many(repository: MongoDBRepository[_Item]) -> None:
    items = [
        _Item(id=str(uuid4()), external_id=str(uuid4())),
        _Item(id=str(uuid4()), external_id=str(uuid4())),
    ]
    assert repository.create_many(items) == items


def test_should_not_duplicate_on_create_many(
    repository: MongoDBRepository[_Item],
) -> None:
    items = [
        _Item(id=str(uuid4()), external_id=str(uuid4())),
        _Item(id=str(uuid4()), external_id=str(uuid4())),
    ]
    repository.create(items[1])
    with pytest.raises(
        ExistsError, match=f"_Item with id<{items[1].id}> already exists."
    ):
        repository.create_many(items)


def test_should_persist(repository: MongoDBRepository[_Item]) -> None:
    item = _Item(id=str(uuid4()), external_id=str(uuid4()))
    repository.create(item)
    assert len(repository) == 1
    assert repository.read(item.id) == item


def test_should_persist_many(repository: MongoDBRepository[_Item]) -> None:
    items = [
        _Item(id=str(uuid4()), external_id=str(uuid4())),
        _Item(id=str(uuid4()), external_id=str(uuid4())),
    ]
    repository.create_many(items)
    assert len(repository) == 2
    assert list(repository) == items


def test_should_persist_update(repository: MongoDBRepository[_Item]) -> None:
    old_item = _Item(id=str(uuid4()), external_id=str(uuid4()))
    repository.create(old_item)
    item = _Item(id=old_item.id, external_id=str(uuid4()))
    repository.update(item)
    assert repository.read(item.id) == item


def test_should_persist_update_many(repository: MongoDBRepository[_Item]) -> None:
    old_items = [
        _Item(id=str(uuid4()), external_id=str(uuid4())),
        _Item(id=str(uuid4()), external_id=str(uuid4())),
    ]
    repository.create_many(old_items)
    items = [
        _Item(id=old_items[0].id, external_id=str(uuid4())),
        _Item(id=old_items[1].id, external_id=str(uuid4())),
    ]
    repository.update_many(items)
    assert list(repository) == items


def test_should_persist_delete(repository: MongoDBRepository[_Item]) -> None:
    items = [
        _Item(id=str(uuid4()), external_id=str(uuid4())),
        _Item(id=str(uuid4()), external_id=str(uuid4())),
    ]
    repository.create_many(items)
    repository.delete(items[1].id)
    assert list(repository) == [items[0]]


def test_should_persist_delete_all(repository: MongoDBRepository[_Item]) -> None:
    items = [
        _Item(id=str(uuid4()), external_id=str(uuid4())),
        _Item(id=str(uuid4()), external_id=str(uuid4())),
    ]
    repository.create_many(items)
    repository.delete_all()
    assert list(repository) == []

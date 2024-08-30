from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, ContextManager
from uuid import uuid4

import mongomock
import pytest
from pymongo import MongoClient

from apexdevkit.error import DoesNotExistError, ExistsError
from apexdevkit.fluent import FluentDict
from apexdevkit.formatter import DataclassFormatter
from apexdevkit.repository import Repository
from apexdevkit.repository.mongo import MongoDatabase, MongoRepository


@dataclass
class _Item:
    external_id: str

    id: str = field(default_factory=lambda: str(uuid4()))


@dataclass
class MongoMockConnector:
    def connect(self) -> ContextManager[MongoClient[Any]]:
        return self._client

    @cached_property
    def _client(self) -> MongoClient[Any]:
        return mongomock.MongoClient()


@pytest.fixture
def repository() -> MongoRepository[_Item]:
    return MongoRepository(
        MongoDatabase(
            MongoMockConnector(),
            "test_database",
            "test_collection",
        ),
        DataclassFormatter(
            resource=lambda **raw: _Item(  # type: ignore
                **FluentDict[Any](raw).select(*_Item.__annotations__.keys())
            )
        ),
    )


def test_should_list_nothing_when_empty(repository: Repository[str, _Item]) -> None:
    assert len(repository) == 0
    assert list(repository) == []


def test_should_not_read_unknown(repository: Repository[str, _Item]) -> None:
    with pytest.raises(DoesNotExistError):
        repository.read(str(uuid4()))


def test_should_create(repository: Repository[str, _Item]) -> None:
    item = _Item(id=str(uuid4()), external_id=str(uuid4()))
    assert repository.create(item) == item


def test_should_not_duplicate_on_create(repository: Repository[str, _Item]) -> None:
    item = _Item(id=str(uuid4()), external_id=str(uuid4()))
    repository.create(item)
    with pytest.raises(ExistsError, match=f"_Item with id<{item.id}> already exists."):
        repository.create(item)


def test_should_create_many(repository: Repository[str, _Item]) -> None:
    items = [
        _Item(id=str(uuid4()), external_id=str(uuid4())),
        _Item(id=str(uuid4()), external_id=str(uuid4())),
    ]
    assert repository.create_many(items) == items


def test_should_not_duplicate_on_create_many(
    repository: Repository[str, _Item],
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


def test_should_persist(repository: Repository[str, _Item]) -> None:
    item = _Item(id=str(uuid4()), external_id=str(uuid4()))
    repository.create(item)
    assert len(repository) == 1
    assert repository.read(item.id) == item


def test_should_persist_many(repository: Repository[str, _Item]) -> None:
    items = [
        _Item(id=str(uuid4()), external_id=str(uuid4())),
        _Item(id=str(uuid4()), external_id=str(uuid4())),
    ]
    repository.create_many(items)
    assert len(repository) == 2
    assert list(repository) == items


def test_should_persist_update(repository: Repository[str, _Item]) -> None:
    old_item = _Item(id=str(uuid4()), external_id=str(uuid4()))
    repository.create(old_item)
    item = _Item(id=old_item.id, external_id=str(uuid4()))
    repository.update(item)
    assert repository.read(item.id) == item


def test_should_persist_update_many(repository: Repository[str, _Item]) -> None:
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


def test_should_persist_delete(repository: Repository[str, _Item]) -> None:
    items = [
        _Item(id=str(uuid4()), external_id=str(uuid4())),
        _Item(id=str(uuid4()), external_id=str(uuid4())),
    ]
    repository.create_many(items)
    repository.delete(items[1].id)
    assert list(repository) == [items[0]]

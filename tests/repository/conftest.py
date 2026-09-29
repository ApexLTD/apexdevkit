import os
from collections.abc import Iterable

import pytest

from apexdevkit.repository import Entity, SqliteRepository
from apexdevkit.repository.sql.sqlite import SqlTable


@pytest.fixture
def repository[T: Entity](table: SqlTable[T]) -> Iterable[SqliteRepository[T]]:
    try:
        yield SqliteRepository(table=table)
    finally:
        os.unlink("test.db")

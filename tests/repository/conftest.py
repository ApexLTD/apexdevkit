from collections.abc import Iterable

import pytest

from apexdevkit.repository import Entity, SqliteRepository
from apexdevkit.repository.sql.sqlite import SqlTable


@pytest.fixture
def repository[T: Entity](table: SqlTable[T]) -> Iterable[SqliteRepository[T]]:
    result = SqliteRepository(table=table)

    try:
        yield result
    finally:
        result.delete_all()

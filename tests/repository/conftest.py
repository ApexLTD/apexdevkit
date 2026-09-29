import os
from collections.abc import Iterable

import pytest

from apexdevkit.repository import Database, Entity, SqliteRepository
from apexdevkit.repository.sql.connector import SqliteFileConnector
from apexdevkit.repository.sql.sqlite import SqlTable


@pytest.fixture
def sqlite_db() -> Iterable[Database]:
    try:
        yield Database(SqliteFileConnector("test.db"))
    finally:
        os.unlink("test.db")


@pytest.fixture
def repository[T: Entity](
    table: SqlTable[T],
    sqlite_db: Database,
) -> SqliteRepository[T]:
    return SqliteRepository(table=table, db=sqlite_db)

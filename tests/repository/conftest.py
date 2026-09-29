import os
from collections.abc import Iterable

import pytest

from apexdevkit.repository import Database
from apexdevkit.repository.sql.connector import SqliteFileConnector


@pytest.fixture
def sqlite_db() -> Iterable[Database]:
    try:
        yield Database(SqliteFileConnector("test.db"))
    finally:
        os.unlink("test.db")

from collections.abc import Iterable
from pathlib import Path

import pytest

from apexdevkit.repository import Database
from apexdevkit.repository.sql.connector import SqliteFileConnector


@pytest.fixture
def sqlite_db() -> Iterable[Database]:
    try:
        yield Database(SqliteFileConnector("test.db"))
    finally:
        Path("test.db").unlink(missing_ok=True)

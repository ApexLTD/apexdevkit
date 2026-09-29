import pytest

from apexdevkit.repository import Database, DatabaseCommand
from apexdevkit.repository.sql.connector import SqliteFileConnector


@pytest.fixture(autouse=True)
def cleanup_db():
    cleanup = DatabaseCommand("DROP TABLE IF EXISTS ITEM;")

    try:
        yield
    finally:
        Database(SqliteFileConnector()).execute(cleanup).fetch_none()

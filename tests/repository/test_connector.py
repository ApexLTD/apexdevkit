from apexdevkit.repository import Connector, DatabaseCommand
from apexdevkit.repository.connector import SqliteFileConnector, SqliteInMemoryConnector

DSN = "test.db"
command = DatabaseCommand("""
    SELECT 1;
""")


def execute_command(connector: Connector) -> None:
    with connector.connect() as connection:
        cursor = connection.cursor()
        cursor.execute(command.value, command.payload)
        cursor.close()


def test_should_connect_to_file() -> None:
    execute_command(SqliteFileConnector(DSN))


def test_should_connect_to_memory() -> None:
    execute_command(SqliteInMemoryConnector())

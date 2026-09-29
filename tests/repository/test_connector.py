from apexdevkit.repository import Connector, DatabaseCommand
from apexdevkit.repository.sql.connector import SqliteFileConnector

command = DatabaseCommand("SELECT 1;")


def execute_command(connector: Connector) -> None:
    with connector.connect() as connection:
        cursor = connection.cursor()
        cursor.execute(command.value, command.payload)
        cursor.close()


def test_should_connect_to_file() -> None:
    execute_command(SqliteFileConnector())

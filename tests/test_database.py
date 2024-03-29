from faker import Faker

from pydevtools.repository import Database, DatabaseCommand
from pydevtools.testing import FakeConnector


def test_should_execute(faker: Faker) -> None:
    connector = FakeConnector()
    command = DatabaseCommand(faker.sentence()).with_data(faker.pydict())

    Database(connector).execute(command).fetch_none()

    connector.assert_contains(command, at_index=0)


def test_should_fetch_one(faker: Faker) -> None:
    expected = faker.pydict()
    connector = FakeConnector().with_result(expected)

    actual = Database(connector).execute(DatabaseCommand("")).fetch_one()

    assert actual == expected


def test_should_fetch_all(faker: Faker) -> None:
    expected = faker.pylist()
    connector = FakeConnector().with_result(expected)

    actual = Database(connector).execute(DatabaseCommand("")).fetch_all()

    assert actual == expected

from faker import Faker

from pydevtools.repository import Database, DatabaseCommand
from pydevtools.testing import FakeConnector


def test_should_execute(faker: Faker) -> None:
    connector = FakeConnector()
    query = faker.sentence()
    data = faker.pydict()

    Database(connector).execute(DatabaseCommand(query).with_data(data)).fetch_none()

    assert connector.commands == [(query, data)]


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

from unittest.mock import ANY

from faker import Faker

from pydevtools.http import JsonObject


def test_should_not_drop_anything(faker: Faker) -> None:
    key = faker.word()

    updated = JsonObject({key: ANY}).drop()

    assert dict(updated) == {key: ANY}


def test_should_drop_a_key(faker: Faker) -> None:
    key = faker.word()

    updated = JsonObject({key: ANY}).drop(key)

    assert dict(updated) == {}


def test_should_drop_many_keys(faker: Faker) -> None:
    key1 = faker.word()
    key2 = faker.word()

    updated = JsonObject({key1: ANY, key2: ANY}).drop(key1, key2)

    assert dict(updated) == {}


def test_should_not_drop_a_key(faker: Faker) -> None:
    key1 = faker.word()
    key2 = faker.word()

    updated = JsonObject({key1: ANY, key2: ANY}).drop(key2)

    assert dict(updated) == {key1: ANY}


def test_should_not_drop_many_keys(faker: Faker) -> None:
    key1 = faker.word()
    key2 = faker.word()
    key3 = faker.word()

    updated = JsonObject({key1: ANY, key2: ANY, key3: ANY}).drop(key3)

    assert dict(updated) == {key1: ANY, key2: ANY}


def test_should_not_select_anything(faker: Faker) -> None:
    key = faker.word()

    updated = JsonObject({key: ANY}).select()

    assert dict(updated) == {}


def test_should_select_a_key(faker: Faker) -> None:
    key = faker.word()

    updated = JsonObject({key: ANY}).select(key)

    assert dict(updated) == {key: ANY}


def test_should_select_many_keys(faker: Faker) -> None:
    key1 = faker.word()
    key2 = faker.word()

    updated = JsonObject({key1: ANY, key2: ANY}).select(key1, key2)

    assert dict(updated) == {key1: ANY, key2: ANY}


def test_should_not_select_a_key(faker: Faker) -> None:
    key1 = faker.word()
    key2 = faker.word()

    updated = JsonObject({key1: ANY, key2: ANY}).select(key1)

    assert dict(updated) == {key1: ANY}


def test_should_not_select_many_keys(faker: Faker) -> None:
    key1 = faker.word()
    key2 = faker.word()
    key3 = faker.word()

    updated = JsonObject({key1: ANY, key2: ANY, key3: ANY}).select(key1)

    assert dict(updated) == {key1: ANY}

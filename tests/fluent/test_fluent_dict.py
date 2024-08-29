from unittest.mock import ANY

from faker import Faker

from apexdevkit.fluent import FluentDict


def test_should_not_drop_anything(faker: Faker) -> None:
    key = faker.word()

    updated = FluentDict({key: ANY}).drop()

    assert dict(updated) == {key: ANY}


def test_should_drop_a_key(faker: Faker) -> None:
    key = faker.word()

    updated = FluentDict({key: ANY}).drop(key)

    assert dict(updated) == {}


def test_should_drop_many_keys(faker: Faker) -> None:
    key1 = faker.word()
    key2 = faker.word()

    updated = FluentDict({key1: ANY, key2: ANY}).drop(key1, key2)

    assert dict(updated) == {}


def test_should_not_drop_a_key(faker: Faker) -> None:
    key1 = faker.word()
    key2 = faker.word()

    updated = FluentDict({key1: ANY, key2: ANY}).drop(key2)

    assert dict(updated) == {key1: ANY}


def test_should_not_drop_many_keys(faker: Faker) -> None:
    key1 = faker.word()
    key2 = faker.word()
    key3 = faker.word()

    updated = FluentDict({key1: ANY, key2: ANY, key3: ANY}).drop(key3)

    assert dict(updated) == {key1: ANY, key2: ANY}


def test_should_not_select_anything(faker: Faker) -> None:
    key = faker.word()

    updated = FluentDict({key: ANY}).select()

    assert dict(updated) == {}


def test_should_select_a_key(faker: Faker) -> None:
    key = faker.word()

    updated = FluentDict({key: ANY}).select(key)

    assert dict(updated) == {key: ANY}


def test_should_select_many_keys(faker: Faker) -> None:
    key1 = faker.word()
    key2 = faker.word()

    updated = FluentDict({key1: ANY, key2: ANY}).select(key1, key2)

    assert dict(updated) == {key1: ANY, key2: ANY}


def test_should_not_select_a_key(faker: Faker) -> None:
    key1 = faker.word()
    key2 = faker.word()

    updated = FluentDict({key1: ANY, key2: ANY}).select(key1)

    assert dict(updated) == {key1: ANY}


def test_should_not_select_many_keys(faker: Faker) -> None:
    key1 = faker.word()
    key2 = faker.word()
    key3 = faker.word()

    updated = FluentDict({key1: ANY, key2: ANY, key3: ANY}).select(key1)

    assert dict(updated) == {key1: ANY}


def test_should_add_a_key(faker: Faker) -> None:
    key = faker.word()
    value = faker.word()

    updated = FluentDict({}).with_a(**{key: value})

    assert dict(updated) == {key: value}


def test_should_merge_empty_json_objects() -> None:
    assert dict(FluentDict({}).merge(FluentDict({}))) == {}


def test_should_merge_json_object_with_empty(faker: Faker) -> None:
    json_object = FluentDict({faker.word(): faker.word()})

    result = json_object.merge(FluentDict({}))

    assert dict(result) == dict(json_object)


def test_should_merge_json_objects_without_overlap(faker: Faker) -> None:
    key1 = faker.word()
    key2 = faker.word()

    result = FluentDict({key1: ANY}).merge(FluentDict({key2: ANY}))

    assert dict(result) == {key1: ANY, key2: ANY}


def test_should_merge_json_objects_with_overlap(faker: Faker) -> None:
    key = faker.word()
    value = faker.word()

    result = FluentDict({key: ANY}).merge(FluentDict({key: value}))

    assert dict(result) == {key: value}

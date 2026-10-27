from __future__ import annotations

from typing import TYPE_CHECKING

from apexdevkit.testing import RestRequest, RestTransport
from tests.fastapi.sample_api import Apple, FakeApple

if TYPE_CHECKING:
    from apexdevkit.fastapi.builder import PreBuilt


def test_should_persist_user_for_create_one(
    transport: RestTransport,
    builder: PreBuilt[Apple],
    username: str,
) -> None:
    RestRequest().with_data(FakeApple().json()).using(transport).create()

    assert builder.user == username


def test_should_persist_user_for_read_one(
    transport: RestTransport,
    builder: PreBuilt[Apple],
    username: str,
) -> None:
    RestRequest().item(with_id=FakeApple().json().get("id")).using(transport).read()

    assert builder.user == username


def test_should_persist_user_for_read_all(
    transport: RestTransport,
    builder: PreBuilt[Apple],
    username: str,
) -> None:
    RestRequest().using(transport).read()

    assert builder.user == username


def test_should_persist_user_for_update_one(
    transport: RestTransport,
    builder: PreBuilt[Apple],
    username: str,
) -> None:
    (
        RestRequest()
        .item(with_id=FakeApple().json().get("id"))
        .with_data(FakeApple().json().drop("id").drop("color"))
        .using(transport)
        .update()
    )

    assert builder.user == username


def test_should_persist_user_for_replace_one(
    transport: RestTransport,
    builder: PreBuilt[Apple],
    username: str,
) -> None:
    RestRequest().with_data(FakeApple().json()).using(transport).replace()

    assert builder.user == username


def test_should_persist_user_for_delete_one(
    transport: RestTransport,
    builder: PreBuilt[Apple],
    username: str,
) -> None:
    RestRequest().item(with_id=FakeApple().json().get("id")).using(transport).delete()

    assert builder.user == username

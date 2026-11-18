from enum import StrEnum
from typing import Annotated

from pydantic import Field
from pypebbles import FluentDict, JsonDict

from apexdevkit.fastapi.name import RestfulName
from apexdevkit.fastapi.schema import RestfulSchema, Schema, SchemaFields
from pytest_apex import ApprovalCase


class Color(StrEnum):
    red = "red"
    green = "green"
    blue = "blue"


class _AppleFields(SchemaFields):
    def readable(self) -> FluentDict[type]:
        return (
            JsonDict()
            .with_a(id=str)
            .and_a(name=str)
            .and_a(color=Annotated[Color, Field(default=Color.red)])
        )


def test_models(approve: ApprovalCase) -> None:
    approve.json().mapping(
        {
            model.__name__: model.model_json_schema()
            for model in RestfulSchema(
                name=RestfulName("apple"),
                fields=_AppleFields(),
                generator=Schema("Apple"),
            )
        }
    )

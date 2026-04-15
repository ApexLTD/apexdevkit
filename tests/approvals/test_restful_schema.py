from enum import StrEnum
from typing import Annotated

from pydantic import Field

from apexdevkit.fastapi.name import RestfulName
from apexdevkit.fastapi.schema import RestfulSchema, Schema, SchemaFields
from apexdevkit.fluent import FluentDict
from apexdevkit.http import JsonDict
from tests.approvals.conftest import Approver


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


def test(approver: Approver) -> None:
    schema = RestfulSchema(
        name=RestfulName("apple"),
        fields=_AppleFields(),
        generator=Schema("apple"),
    )

    for name, model in schema.schemas.items():
        approver.verify_json(name or "Root", model.model_json_schema())

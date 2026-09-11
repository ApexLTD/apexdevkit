from abc import ABC, abstractmethod
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from functools import cached_property
from typing import Any

from pydantic import BaseModel, create_model
from pypebbles import FluentDict

from apexdevkit.fastapi.name import RestfulName


class SchemaFields(ABC):
    def id(self) -> FluentDict[type]:
        return self.readable().select("id")

    def writable(self) -> FluentDict[type]:
        return self.readable().drop("id")

    def editable(self) -> FluentDict[type]:
        return self.readable().drop("id")

    @abstractmethod
    def readable(self) -> FluentDict[type]:  # pragma: no cover
        pass


@dataclass(frozen=True)
class RestfulSchema:
    name: RestfulName
    fields: SchemaFields
    generator: "Schema"

    def __post_init__(self) -> None:
        schema = self._schema_for("", self.fields.readable())

        self._schema_for("Create", self.fields.writable())
        self._schema_for("Update", self.fields.editable())
        self._schema_for("Replace", self.fields.readable())
        self._schema_for("Item", {self.name.singular: schema})
        self._schema_for("Collection", {self.name.plural: list[schema], "count": int})

    def _schema_for(self, action: str, fields: dict[str, Any]) -> type[BaseModel]:
        if action not in self._models:
            self._models[action] = self.generator.schema_for(action, fields)

        return self._models[action]

    @cached_property
    def _models(self) -> dict[str, type[BaseModel]]:
        return {}

    def __iter__(self) -> Iterator[type[BaseModel]]:
        return iter(self._models.values())

    def for_no_data(self) -> type[BaseModel]:
        class NoData(BaseModel):
            pass

        return self._schema_for(
            "NoDataResponse",
            FluentDict[type]().with_a(status=str).and_a(code=int).and_a(data=NoData),
        )

    def for_item(self) -> type[BaseModel]:
        return self._schema_for(
            "ItemResponse",
            FluentDict[type]()
            .with_a(status=str)
            .and_a(code=int)
            .and_a(data=self._models["Item"]),
        )

    def for_collection(self) -> type[BaseModel]:
        return self._schema_for(
            "CollectionResponse",
            FluentDict[type]()
            .with_a(status=str)
            .and_a(code=int)
            .and_a(data=self._models["Collection"]),
        )

    def for_create_one(self) -> Callable[[BaseModel], dict[str, Any]]:
        schema = self._models["Create"]

        def _(request: schema) -> dict[str, Any]:
            return request.model_dump()

        return _

    def for_update_one(self) -> Callable[[BaseModel], dict[str, Any]]:
        schema = self._models["Update"]

        def _(request: schema):
            return request.model_dump()

        return _

    def for_replace_one(self) -> Callable[[BaseModel], dict[str, Any]]:
        schema = self._models["Replace"]

        def _(request: schema) -> dict[str, Any]:
            return request.model_dump()

        return _


@dataclass(frozen=True)
class Schema:
    resource: str

    def schema_for(self, action: str, fields: dict[str, Any]) -> type[BaseModel]:
        return self._nested_schema_for(self.resource + action, fields)

    def optional_schema_for(
        self, action: str, fields: dict[str, Any]
    ) -> type[BaseModel]:
        return create_model(
            self.resource + action,
            **{
                field_name: (field_type | None, None)
                for field_name, field_type in fields.items()
            },
        )

    def _nested_schema_for(self, name: str, fields: dict[str, Any]) -> type[BaseModel]:
        model_fields = {}

        for field_name, field_type in fields.items():
            if isinstance(field_type, dict):
                model_fields[field_name] = self._nested_schema_for(
                    name + field_name.capitalize(),
                    field_type,
                )
            else:
                model_fields[field_name] = field_type

        return create_model(name, **model_fields)

from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from functools import cached_property
from typing import Any

from pydantic import BaseModel, create_model

from apexdevkit.fastapi.name import RestfulName
from apexdevkit.fluent import FluentDict
from apexdevkit.http import JsonDict


class SchemaFields(ABC):
    def id(self) -> FluentDict[type]:
        return self.readable().select("id")

    def writable(self) -> FluentDict[type]:
        return self.readable().drop("id")

    def editable(self) -> FluentDict[type]:
        return self.readable().drop("id")

    def filters(self) -> FluentDict[type]:
        return JsonDict()

    def sum_filters(self) -> FluentDict[type]:
        return JsonDict()

    @abstractmethod
    def readable(self) -> FluentDict[type]:  # pragma: no cover
        pass


@dataclass(frozen=True)
class RestfulSchema:
    name: RestfulName
    fields: SchemaFields

    def __post_init__(self) -> None:
        schema = self._schema_for("", self.fields.readable())
        create_schema = self._schema_for("Create", self.fields.writable())
        self._schema_for("Update", self.fields.editable())
        replace_schema = self._schema_for("Replace", self.fields.readable())
        update_many_item = self._schema_for(
            "UpdateManyItem", self.fields.editable().merge(self.fields.id())
        )
        self._schema_for("Filter", self.fields.filters())
        self._schema_for("Sum", self.fields.sum_filters())

        self._schema_for("Item", {self.name.singular: schema})
        self._schema_for("Collection", {self.name.plural: list[schema], "count": int})
        self._schema_for("CreateMany", {self.name.plural: list[create_schema]})
        self._schema_for("UpdateMany", {self.name.plural: list[update_many_item]})
        self._schema_for("ReplaceMany", {self.name.plural: list[replace_schema]})

    def _schema_for(self, action: str, fields: dict[str, Any]) -> type[BaseModel]:
        if action not in self.schemas:
            self.schemas[action] = Schema(self.name).schema_for(action, fields)

        return self.schemas[action]

    @cached_property
    def schemas(self) -> dict[str, type[BaseModel]]:
        return {}

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
            .and_a(data=self.schemas["Item"]),
        )

    def for_collection(self) -> type[BaseModel]:
        return self._schema_for(
            "CollectionResponse",
            FluentDict[type]()
            .with_a(status=str)
            .and_a(code=int)
            .and_a(data=self.schemas["Collection"]),
        )

    def for_create_one(self) -> Callable[[BaseModel], dict[str, Any]]:
        schema = self.schemas["Create"]

        def _(request: schema) -> dict[str, Any]:
            return request.model_dump()

        return _

    def for_create_many(self) -> Callable[[BaseModel], Iterable[dict[str, Any]]]:
        schema = self.schemas["CreateMany"]

        def _(request: schema) -> Iterable[dict[str, Any]]:
            return [dict(item) for item in request.model_dump()[self.name.plural]]

        return _

    def for_update_one(self) -> Callable[[BaseModel], dict[str, Any]]:
        schema = self.schemas["Update"]

        def _(request: schema):
            return request.model_dump()

        return _

    def for_update_many(self) -> Callable[[BaseModel], Iterable[dict[str, Any]]]:
        schema = self.schemas["UpdateMany"]

        def _(request: schema) -> Iterable[dict[str, Any]]:
            return [dict(item) for item in request.model_dump()[self.name.plural]]

        return _

    def for_replace_one(self) -> Callable[[BaseModel], dict[str, Any]]:
        schema = self.schemas["Replace"]

        def _(request: schema) -> dict[str, Any]:
            return request.model_dump()

        return _

    def for_replace_many(self) -> Callable[[BaseModel], Iterable[dict[str, Any]]]:
        schema = self.schemas["ReplaceMany"]

        def _(request: schema) -> Iterable[dict[str, Any]]:
            return [dict(item) for item in request.model_dump()[self.name.plural]]

        return _

    def for_filters(self) -> Callable[[BaseModel], dict[str, Any]]:
        schema = self.schemas["Filter"]

        def _(request: schema) -> dict[str, Any]:
            return request.model_dump()

        return _

    def for_sum(self) -> Callable[[BaseModel], dict[str, Any]]:
        schema = self.schemas["Sum"]

        def _(request: schema) -> dict[str, Any]:
            return request.model_dump()

        return _


@dataclass(frozen=True)
class Schema:
    name: RestfulName

    def schema_for(self, action: str, fields: dict[str, Any]) -> type[BaseModel]:
        return self._nested_schema_for(self.name.singular.capitalize() + action, fields)

    def optional_schema_for(
        self, action: str, fields: dict[str, Any]
    ) -> type[BaseModel]:
        return create_model(
            self.name.singular.capitalize() + action,
            **{
                field_name: (field_type | None, None)
                for field_name, field_type in fields.items()
            },
        )

    def _nested_schema_for(self, name: str, fields: dict[str, Any]) -> type[BaseModel]:
        model_fields = {}

        for field_name, field_type in fields.items():
            if isinstance(field_type, dict):
                model_fields[field_name] = (
                    self._nested_schema_for(
                        name.capitalize() + field_name.capitalize(), field_type
                    ),
                    ...,
                )
            else:
                model_fields[field_name] = (field_type, ...)

        return create_model(name, **model_fields)

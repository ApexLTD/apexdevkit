from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from functools import cached_property
from typing import Any

from pydantic import BaseModel, create_model

from apexdevkit.fastapi.name import RestfulName
from apexdevkit.fluent import FluentDict
from apexdevkit.http import JsonDict
from apexdevkit.value import Value


class AggregationResult(BaseModel):
    field: str
    aggregation: Value


class SchemaFields(ABC):
    def id(self) -> FluentDict[type]:
        return self.readable().select("id")

    def writable(self) -> FluentDict[type]:
        return self.readable().drop("id")

    def editable(self) -> FluentDict[type]:
        return self.readable().drop("id")

    def filters(self) -> FluentDict[type]:
        return JsonDict()

    def aggregation_filters(self) -> FluentDict[type]:
        return JsonDict()

    def aggregation_result(self) -> FluentDict[type]:
        return JsonDict().with_a(count=int).and_a(sums=list[AggregationResult])

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
        create_schema = self._schema_for("Create", self.fields.writable())
        self._schema_for("Update", self.fields.editable())
        replace_schema = self._schema_for("Replace", self.fields.readable())
        update_many_item = self._schema_for(
            "UpdateManyItem", self.fields.editable().merge(self.fields.id())
        )
        self._schema_for("Filter", self.fields.filters())
        self._schema_for("Aggregation", self.fields.aggregation_filters())
        self._schema_for("AggregationResult", self.fields.aggregation_result())

        self._schema_for("Item", {self.name.singular: schema})
        self._schema_for("Collection", {self.name.plural: list[schema], "count": int})
        self._schema_for("CreateMany", {self.name.plural: list[create_schema]})
        self._schema_for("UpdateMany", {self.name.plural: list[update_many_item]})
        self._schema_for("ReplaceMany", {self.name.plural: list[replace_schema]})

    def _schema_for(self, action: str, fields: dict[str, Any]) -> type[BaseModel]:
        if action not in self._models:
            self._models[action] = self.generator.schema_for(action, fields)

        return self._models[action]

    @cached_property
    def _models(self) -> dict[str, type[BaseModel]]:
        return {}

    def __iter__(self) -> Iterable[type[BaseModel]]:
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

    def for_create_many(self) -> Callable[[BaseModel], Iterable[dict[str, Any]]]:
        schema = self._models["CreateMany"]

        def _(request: schema) -> Iterable[dict[str, Any]]:
            return [dict(item) for item in request.model_dump()[self.name.plural]]

        return _

    def for_update_one(self) -> Callable[[BaseModel], dict[str, Any]]:
        schema = self._models["Update"]

        def _(request: schema):
            return request.model_dump()

        return _

    def for_update_many(self) -> Callable[[BaseModel], Iterable[dict[str, Any]]]:
        schema = self._models["UpdateMany"]

        def _(request: schema) -> Iterable[dict[str, Any]]:
            return [dict(item) for item in request.model_dump()[self.name.plural]]

        return _

    def for_replace_one(self) -> Callable[[BaseModel], dict[str, Any]]:
        schema = self._models["Replace"]

        def _(request: schema) -> dict[str, Any]:
            return request.model_dump()

        return _

    def for_replace_many(self) -> Callable[[BaseModel], Iterable[dict[str, Any]]]:
        schema = self._models["ReplaceMany"]

        def _(request: schema) -> Iterable[dict[str, Any]]:
            return [dict(item) for item in request.model_dump()[self.name.plural]]

        return _

    def for_filters(self) -> Callable[[BaseModel], dict[str, Any]]:
        schema = self._models["Filter"]

        def _(request: schema) -> dict[str, Any]:
            return request.model_dump()

        return _

    def for_aggregation(self) -> Callable[[BaseModel], dict[str, Any]]:
        schema = self._models["Aggregation"]

        def _(request: schema) -> dict[str, Any]:
            return request.model_dump()

        return _

    def for_aggregation_result(self) -> type[BaseModel]:
        return self._schema_for(
            "AggregationResultResponse",
            FluentDict[type]()
            .with_a(status=str)
            .and_a(code=int)
            .and_a(aggregations=self._models["AggregationResult"]),
        )


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

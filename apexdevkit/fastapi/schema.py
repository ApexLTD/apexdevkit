from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import cached_property
from typing import Any, Callable, Iterable, List

from pydantic import BaseModel, create_model

from apexdevkit.http import JsonDict
from apexdevkit.testing import RestfulName


class SchemaFields(ABC):
    def writable(self) -> JsonDict:
        return self.readable().drop("id")

    def editable(self) -> JsonDict:
        return self.readable().drop("id")

    @abstractmethod
    def readable(self) -> JsonDict:
        pass


@dataclass
class DataclassFields(SchemaFields):
    source: Any

    def readable(self) -> JsonDict:
        return JsonDict(self.source.__annotations__)


@dataclass
class RestfulSchema:
    name: RestfulName
    fields: SchemaFields

    def __post_init__(self) -> None:
        schema = self._schema_for("", self.fields.readable())
        create_schema = self._schema_for("Create", self.fields.writable())
        self._schema_for("Update", self.fields.editable())

        self._schema_for(
            "Item",
            JsonDict({self.name.singular: schema}),
        )
        self._schema_for(
            "Collection",
            JsonDict({self.name.plural: List[schema]}).with_a(count=int),
        )

        self._schema_for(
            "CreateMany",
            JsonDict({self.name.plural: List[create_schema]}),
        )
        self._schema_for(
            "UpdateMany",
            JsonDict({self.name.plural: List[schema]}),
        )

    def _schema_for(self, action: str, fields: dict[str, Any]) -> type[BaseModel]:
        if action not in self.schemas:
            self.schemas[action] = create_model(
                self.name.singular.capitalize() + action,
                **{
                    field_name: (field_type, ...)
                    for field_name, field_type in fields.items()
                },
            )

        return self.schemas[action]

    @cached_property
    def schemas(self) -> dict[str, type[BaseModel]]:
        return {}

    def for_no_data(self) -> type[BaseModel]:
        class NoData(BaseModel):
            pass

        return self._schema_for(
            "NoDataResponse",
            JsonDict().with_a(status=str).and_a(code=int).and_a(data=NoData),
        )

    def for_item(self) -> type[BaseModel]:
        return self._schema_for(
            "ItemResponse",
            JsonDict()
            .with_a(status=str)
            .and_a(code=int)
            .and_a(data=self.schemas["Item"]),
        )

    def for_collection(self) -> type[BaseModel]:
        return self._schema_for(
            "CollectionResponse",
            JsonDict()
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

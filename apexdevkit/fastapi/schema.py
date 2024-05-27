from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, List

from pydantic import BaseModel, create_model

from apexdevkit.http import JsonDict
from apexdevkit.testing import RestfulName


@dataclass
class RestfulSchema:
    name: RestfulName
    fields: JsonDict

    schemas: dict[str, type[BaseModel]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        schema = self._schema_for("", self.fields)
        create_schema = self._schema_for("Create", self.fields.drop("id"))
        self._schema_for("Update", self.fields.drop("id"))

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

    @classmethod
    def from_dataclass(cls, value: Any) -> "RestfulSchema":
        return cls(
            name=RestfulName(value.__name__.lower()),
            fields=JsonDict(value.__annotations__),
        )

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

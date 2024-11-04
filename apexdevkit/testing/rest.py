from __future__ import annotations

from dataclasses import dataclass

from apexdevkit.fastapi.name import RestfulName
from apexdevkit.fastapi.rest import RestResource


@dataclass(frozen=True)
class RestCollection(RestResource):
    def sub_resource(self, name: str) -> RestItem:
        return RestItem(self.http.with_endpoint(self.name.plural), RestfulName(name))


@dataclass(frozen=True)
class RestItem(RestResource):
    def sub_resource(self, name: str) -> RestItem:
        return RestItem(self.http.with_endpoint(self.name.singular), RestfulName(name))

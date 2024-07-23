from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from apexdevkit.error import DoesNotExistError, ExistsError, ForbiddenError
from apexdevkit.testing import RestfulName


@dataclass
class RestfulResponse:
    name: RestfulName

    def _response(self, code: int, data: Any, error: str = "") -> dict[str, Any]:
        content: dict[str, Any] = {"code": code, "status": "success"}

        if error:
            content["status"] = "fail"
            content["error"] = {"message": error}

        match data:
            case None:
                content["data"] = {}
            case list():
                content["data"] = {self.name.plural: data, "count": len(data)}
            case _:
                content["data"] = {self.name.singular: data}

        return content

    def ok(self) -> dict[str, Any]:
        return self._response(200, data=None)

    def not_found(self, e: DoesNotExistError) -> dict[str, Any]:
        name = self.name.singular.capitalize()

        return self._response(
            404,
            data={"id": str(e.id)},
            error=f"An item<{name}> with id<{e.id}> does not exist.",
        )

    def exists(self, e: ExistsError) -> dict[str, Any]:
        name = self.name.singular.capitalize()

        return self._response(
            409,
            data={"id": str(e.id)},
            error=f"An item<{name}> with the {e} already exists.",
        )

    def forbidden(self, e: ForbiddenError) -> dict[str, Any]:
        return self._response(
            403,
            data={"id": str(e.id)},
            error=e.message,
        )

    def created_one(self, item: Any) -> dict[str, Any]:
        return self._response(201, item)

    def created_many(self, items: Iterable[Any]) -> dict[str, Any]:
        return self._response(201, list(items))

    def found_one(self, item: Any) -> dict[str, Any]:
        return self._response(200, item)

    def found_many(self, items: list[Any]) -> dict[str, Any]:
        return self._response(200, items)

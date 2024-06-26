from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from fastapi import status
from fastapi.responses import JSONResponse

from apexdevkit.error import DoesNotExistError, ExistsError, ForbiddenError
from apexdevkit.testing import RestfulName


class SuccessResponse(dict[str, Any]):
    def __init__(self, status_code: int, **kwargs: Any):
        super().__init__(
            {
                "status": "success",
                "code": status_code,
                "data": {**kwargs},
            }
        )


class ResourceFound(SuccessResponse):
    def __init__(self, **kwargs: Any):
        super().__init__(status_code=status.HTTP_200_OK, **kwargs)


class ResourceCreated(SuccessResponse):
    def __init__(self, **kwargs: Any):
        super().__init__(status_code=status.HTTP_201_CREATED, **kwargs)


class ErrorResponse(JSONResponse):
    def __init__(self, status_code: int, message: str, **kwargs: Any):
        content = {
            "status": "fail",
            "code": status_code,
            "error": {"message": message},
        }

        if kwargs:
            content["data"] = {**kwargs}

        super().__init__(status_code=status_code, content=content)


class BadRequest(ErrorResponse):
    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=message,
            **kwargs,
        )


class ResourceNotFound(ErrorResponse):
    def __init__(self, message: str):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, message=message)


class ResourceExists(ErrorResponse):
    def __init__(self, message: str, **kwargs: Any):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            message=message,
            **kwargs,
        )


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

from __future__ import annotations

from typing import Any

from fastapi import status
from fastapi.responses import JSONResponse


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

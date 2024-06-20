from typing import Any

from fastapi import Depends
from fastapi.requests import Request


def inject(dependency: str) -> Any:  # pragma: no cover
    def get(request: Request) -> Any:
        return getattr(request.app.state, dependency)

    return Depends(get)

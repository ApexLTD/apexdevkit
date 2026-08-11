from __future__ import annotations

from typing import Protocol

from .method import HttpMethod
from .request import HttpRequest
from .response import HttpResponse


class HttpTransporter(Protocol):
    def __call__(self, method: HttpMethod) -> HttpTransporter:
        pass

    def over(self, method: HttpMethod) -> HttpTransporter:
        pass

    def transport(self, request: HttpRequest) -> HttpResponse:
        pass

from __future__ import annotations

from typing import Protocol

from .method import HttpMethod
from .request import HttpRequest
from .response import HttpResponse


class HttpChannel(Protocol):
    def transport(self, request: HttpRequest) -> HttpTransport:
        pass


class HttpTransport(Protocol):
    def over(self, method: HttpMethod) -> HttpResponse:
        pass

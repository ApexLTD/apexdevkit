from __future__ import annotations

from dataclasses import dataclass, field, replace

from pypebbles import FluentDict
from pypebbles.runtime import Environment

from . import HttpUrl
from .domain import HttpMethod, HttpRequest, HttpResponse


@dataclass(frozen=True)
class InternalEcho:
    method: HttpMethod = HttpMethod.get
    headers: FluentDict[str] = field(default_factory=FluentDict[str])

    server: str = Environment().inject(
        variable="ECHO_SERVER",
        default="http://localhost:8080",
    )

    def __call__(self, method: HttpMethod) -> InternalEcho:
        return self.over(method)

    def over(self, method: HttpMethod) -> InternalEcho:
        return replace(self, method=method)

    def transport(self, request: HttpRequest) -> HttpResponse:
        if request.endpoint != self.method.name:
            return HttpResponse(status=403).set_json({"method": request.endpoint})

        return HttpResponse(status=200).set_json(
            {
                "url": HttpUrl(self.server) + request.query,
                "headers": request.headers.merge(self.headers),
                "params": request.params,
                "json": request.json,
                "form": request.data,
            }
        )

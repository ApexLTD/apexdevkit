from __future__ import annotations

from dataclasses import dataclass, replace

from .domain import HttpMethod, HttpRequest, HttpResponse


@dataclass(frozen=True)
class InternalEcho:
    method: HttpMethod = HttpMethod.get

    def __call__(self, method: HttpMethod) -> InternalEcho:
        return self.over(method)

    def over(self, method: HttpMethod) -> InternalEcho:
        return replace(self, method=method)

    def transport(self, request: HttpRequest) -> HttpResponse:
        return HttpResponse(status=200).set_json(
            {
                "method": self.method.name,
                "endpoint": request.endpoint,
                "headers": request.headers,
                "params": request.params,
                "json": request.json,
                "data": request.data,
            }
        )

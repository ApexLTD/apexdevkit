from __future__ import annotations

from dataclasses import dataclass, field, replace

from .domain import HttpMethod, HttpRequest, HttpResponse


@dataclass(frozen=True)
class InternalEcho:
    _request: HttpRequest = field(default_factory=HttpRequest)

    def transport(self, request: HttpRequest) -> InternalEcho:
        return replace(self, _request=request)

    def over(self, method: HttpMethod) -> HttpResponse:
        return HttpResponse(status=200).set_json(
            {
                "method": method.name,
                "endpoint": self._request.endpoint,
                "headers": self._request.headers,
                "params": self._request.params,
                "json": self._request.json,
                "data": self._request.data,
            }
        )

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar

import httpx

ContextT = TypeVar("ContextT", contravariant=True)


class HttpxHandler(Protocol[ContextT]):
    def on_get(self, context: ContextT) -> None:
        pass

    def on_post(self, context: ContextT) -> None:
        pass

    def on_patch(self, context: ContextT) -> None:
        pass

    def on_delete(self, context: ContextT) -> None:
        pass


class DefaultHandler(Generic[ContextT]):
    def on_get(self, context: ContextT) -> None:
        pass

    def on_post(self, context: ContextT) -> None:
        pass

    def on_patch(self, context: ContextT) -> None:
        pass

    def on_delete(self, context: ContextT) -> None:
        pass


@dataclass(frozen=True)
class BeforeRequestHook:
    handler: HttpxHandler[httpx.Request]

    def __call__(self, request: httpx.Request) -> None:
        match request.method.upper():
            case "GET":
                self.handler.on_get(request)
            case "POST":
                self.handler.on_post(request)
            case "PATCH":
                self.handler.on_patch(request)
            case "DELETE":
                self.handler.on_delete(request)
            case _:
                pass


@dataclass(frozen=True)
class AfterResponseHook:
    handler: HttpxHandler[httpx.Response]

    def __call__(self, response: httpx.Response) -> None:
        match response.request.method.upper():
            case "GET":
                self.handler.on_get(response)
            case "POST":
                self.handler.on_post(response)
            case "PATCH":
                self.handler.on_patch(response)
            case "DELETE":
                self.handler.on_delete(response)
            case _:
                pass

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, TypeVar

from httpx2 import Request, Response, SyncByteStream

from apexdevkit.security import Authority

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


class DefaultHandler[ContextT]:
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
    handler: HttpxHandler[Request]

    def __call__(self, request: Request) -> None:
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
    handler: HttpxHandler[Response]

    def __call__(self, response: Response) -> None:
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


@dataclass(frozen=True)
class SignPayloadWith(DefaultHandler[Request]):
    authority: Authority

    def on_post(self, context: Request) -> None:
        assert isinstance(context.stream, SyncByteStream)
        signature = self.authority.sign(next(iter(context.stream)).decode())
        context.headers[signature.name] = signature.value

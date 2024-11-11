from dataclasses import dataclass
from typing import Any, Callable

from starlette.responses import JSONResponse

from apexdevkit.error import DoesNotExistError, ExistsError, ForbiddenError
from apexdevkit.fastapi.response import RestfulResponse

_Response = JSONResponse | dict[str, Any]
_Endpoint = Callable[..., _Response]


@dataclass(frozen=True)
class RestfulResource:
    response: RestfulResponse

    def create_one(self, Service, Item) -> _Endpoint:  # type: ignore
        def endpoint(service: Service, item: Item) -> _Response:
            try:
                item = service.create_one(item)
            except ExistsError as e:
                return JSONResponse(self.response.exists(e), 409)
            except ForbiddenError as e:
                return JSONResponse(self.response.forbidden(e), 403)

            return self.response.created_one(item)

        return endpoint

    def create_many(self, Service, Collection) -> _Endpoint:  # type: ignore
        def endpoint(service: Service, items: Collection) -> _Response:
            try:
                return self.response.created_many(service.create_many(items))
            except ExistsError as e:
                return JSONResponse(self.response.exists(e), 409)
            except ForbiddenError as e:
                return JSONResponse(self.response.forbidden(e), 403)

        return endpoint

    def read_one(self, Service, ItemId) -> _Endpoint:  # type: ignore
        def endpoint(service: Service, item_id: ItemId) -> _Response:
            try:
                return self.response.found_one(service.read_one(item_id))
            except DoesNotExistError as e:
                return JSONResponse(self.response.not_found(e), 404)
            except ForbiddenError as e:
                return JSONResponse(self.response.forbidden(e), 403)

        return endpoint

    def read_many(self, Service, QueryParams) -> _Endpoint:  # type: ignore
        def endpoint(service: Service, params: QueryParams) -> _Response:
            try:
                return self.response.found_many(list(service.read_many(**dict(params))))
            except ForbiddenError as e:
                return JSONResponse(self.response.forbidden(e), 403)

        return endpoint

    def read_all(self, Service) -> _Endpoint:  # type: ignore
        def endpoint(service: Service) -> _Response:
            try:
                return self.response.found_many(list(service.read_all()))
            except ForbiddenError as e:
                return JSONResponse(self.response.forbidden(e), 403)

        return endpoint

    def update_one(self, Service, ItemId, Updates) -> _Endpoint:  # type: ignore
        def endpoint(service: Service, item_id: ItemId, updates: Updates) -> _Response:
            try:
                service.update_one(item_id, **updates)
            except DoesNotExistError as e:
                return JSONResponse(self.response.not_found(e), 404)
            except ForbiddenError as e:
                return JSONResponse(self.response.forbidden(e), 403)

            return self.response.ok()

        return endpoint

    def update_many(self, Service, Collection) -> _Endpoint:  # type: ignore
        def endpoint(service: Service, items: Collection) -> _Response:
            try:
                service.update_many(items)
            except DoesNotExistError as e:
                return JSONResponse(self.response.not_found(e), 404)
            except ForbiddenError as e:
                return JSONResponse(self.response.forbidden(e), 403)

            return self.response.ok()

        return endpoint

    def replace_one(self, Service, Item) -> _Endpoint:  # type: ignore
        def endpoint(service: Service, item: Item) -> _Response:
            try:
                service.replace_one(item)
            except DoesNotExistError as e:
                return JSONResponse(self.response.not_found(e), 404)
            except ForbiddenError as e:
                return JSONResponse(self.response.forbidden(e), 403)

            return self.response.ok()

        return endpoint

    def replace_many(self, Service, Collection) -> _Endpoint:  # type: ignore
        def endpoint(service: Service, items: Collection) -> _Response:
            try:
                service.replace_many(items)
            except DoesNotExistError as e:
                return JSONResponse(self.response.not_found(e), 404)
            except ForbiddenError as e:
                return JSONResponse(self.response.forbidden(e), 403)

            return self.response.ok()

        return endpoint

    def delete_one(self, Service, ItemId) -> _Endpoint:  # type: ignore
        def endpoint(service: Service, item_id: ItemId) -> _Response:
            try:
                service.delete_one(item_id)
            except DoesNotExistError as e:
                return JSONResponse(self.response.not_found(e), 404)
            except ForbiddenError as e:
                return JSONResponse(self.response.forbidden(e), 403)

            return self.response.ok()

        return endpoint

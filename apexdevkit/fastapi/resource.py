from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from fastapi.responses import JSONResponse

from apexdevkit.error import DoesNotExistError, ExistsError, ForbiddenError
from apexdevkit.fastapi.response import RestfulResponse

_Response = JSONResponse | dict[str, Any]
_Endpoint = Callable[..., _Response]


@dataclass(frozen=True)
class RestfulResource:
    response: RestfulResponse

    def create_one_endpoint(self, Service, Item) -> _Endpoint:
        def endpoint(service: Service, item: Item) -> _Response:
            try:
                result = service.create_one(item)
            except ExistsError as e:
                return JSONResponse(self.response.exists(e), 409)
            except ForbiddenError as e:
                return JSONResponse(self.response.forbidden(e), 403)

            return self.response.created_one(result)

        return endpoint

    def read_one_endpoint(self, Service, ItemId) -> _Endpoint:
        def endpoint(service: Service, item_id: ItemId) -> _Response:
            try:
                result = service.read_one(item_id)
            except DoesNotExistError as e:
                return JSONResponse(self.response.not_found(e), 404)
            except ForbiddenError as e:
                return JSONResponse(self.response.forbidden(e), 403)

            return self.response.found_one(result)

        return endpoint

    def read_many_endpoint(self, Service, QueryParams) -> _Endpoint:
        def endpoint(service: Service, params: QueryParams) -> _Response:
            try:
                result = list(service.read_many(**dict(params)))
            except ForbiddenError as e:
                return JSONResponse(self.response.forbidden(e), 403)

            return self.response.found_many(result)

        return endpoint

    def read_all_endpoint(self, Service) -> _Endpoint:
        def endpoint(service: Service) -> _Response:
            try:
                result = list(service.read_all())
            except ForbiddenError as e:
                return JSONResponse(self.response.forbidden(e), 403)

            return self.response.found_many(result)

        return endpoint

    def update_one_endpoint(self, Service, ItemId, Updates) -> _Endpoint:
        def endpoint(service: Service, item_id: ItemId, updates: Updates) -> _Response:
            try:
                service.update_one(item_id, **updates)
            except DoesNotExistError as e:
                return JSONResponse(self.response.not_found(e), 404)
            except ForbiddenError as e:
                return JSONResponse(self.response.forbidden(e), 403)

            return self.response.ok()

        return endpoint

    def replace_one_endpoint(self, Service, Item) -> _Endpoint:
        def endpoint(service: Service, item: Item) -> _Response:
            try:
                service.replace_one(item)
            except DoesNotExistError as e:
                return JSONResponse(self.response.not_found(e), 404)
            except ForbiddenError as e:
                return JSONResponse(self.response.forbidden(e), 403)

            return self.response.ok()

        return endpoint

    def delete_one_endpoint(self, Service, ItemId) -> _Endpoint:
        def endpoint(service: Service, item_id: ItemId) -> _Response:
            try:
                service.delete_one(item_id)
            except DoesNotExistError as e:
                return JSONResponse(self.response.not_found(e), 404)
            except ForbiddenError as e:
                return JSONResponse(self.response.forbidden(e), 403)

            return self.response.ok()

        return endpoint

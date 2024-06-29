from dataclasses import dataclass
from functools import cached_property
from typing import Any, Callable, Annotated

from fastapi import Path
from starlette.responses import JSONResponse

from apexdevkit.error import DoesNotExistError, ExistsError, ForbiddenError
from apexdevkit.fastapi.builder import RestfulServiceBuilder
from apexdevkit.fastapi.response import RestfulResponse
from apexdevkit.testing import RestfulName

_Response = JSONResponse | dict[str, Any]


@dataclass
class RestfulSubResource:
    name: RestfulName
    infra: RestfulServiceBuilder
    parent: RestfulName

    @property
    def parent_id_alias(self) -> str:
        return self.parent.singular + "_id"

    @cached_property
    def response(self) -> RestfulResponse:
        return RestfulResponse(name=self.name)

    def create_one(self, User, Item) -> Callable[..., _Response]:  # type: ignore
        ParentId = Annotated[str, Path(alias=self.parent_id_alias)]

        def endpoint(user: User, parent_id: ParentId, item: Item) -> _Response:
            try:
                service = self.infra.with_user(user).with_parent(parent_id).build()
            except DoesNotExistError as e:
                return JSONResponse(RestfulResponse(self.parent).not_found(e), 404)

            try:
                item = service.create_one(item)
            except ExistsError as e:
                return JSONResponse(self.response.exists(e), 409)
            except ForbiddenError as e:
                return JSONResponse(self.response.forbidden(e), 403)

            return self.response.created_one(item)

        return endpoint

    def create_many(self, User, Collection) -> Callable[..., _Response]:  # type: ignore
        ParentId = Annotated[str, Path(alias=self.parent_id_alias)]

        def endpoint(user: User, parent_id: ParentId, items: Collection) -> _Response:
            try:
                service = self.infra.with_user(user).with_parent(parent_id).build()
            except DoesNotExistError as e:
                return JSONResponse(RestfulResponse(self.parent).not_found(e), 404)

            try:
                return self.response.created_many(service.create_many(items))
            except ExistsError as e:
                return JSONResponse(self.response.exists(e), 409)
            except ForbiddenError as e:
                return JSONResponse(self.response.forbidden(e), 403)

        return endpoint

    def read_one(self, User, ItemId) -> Callable[..., _Response]:  # type: ignore
        ParentId = Annotated[str, Path(alias=self.parent_id_alias)]

        def endpoint(user: User, parent_id: ParentId, item_id: ItemId) -> _Response:
            try:
                service = self.infra.with_user(user).with_parent(parent_id).build()
            except DoesNotExistError as e:
                return JSONResponse(RestfulResponse(self.parent).not_found(e), 404)

            try:
                return self.response.found_one(service.read_one(item_id))
            except DoesNotExistError as e:
                return JSONResponse(self.response.not_found(e), 404)
            except ForbiddenError as e:
                return JSONResponse(self.response.forbidden(e), 403)

        return endpoint

    def read_all(self, User) -> Callable[..., _Response]:  # type: ignore
        ParentId = Annotated[str, Path(alias=self.parent_id_alias)]

        def endpoint(user: User, parent_id: ParentId) -> _Response:
            try:
                service = self.infra.with_user(user).with_parent(parent_id).build()
            except DoesNotExistError as e:
                return JSONResponse(RestfulResponse(self.parent).not_found(e), 404)

            try:
                return self.response.found_many(list(service.read_all()))
            except ForbiddenError as e:
                return JSONResponse(self.response.forbidden(e), 403)

        return endpoint

    def update_one(self, User, ItemId, Updates) -> Callable[..., _Response]:  # type: ignore
        ParentId = Annotated[str, Path(alias=self.parent_id_alias)]

        def endpoint(
            user: User,
            parent_id: ParentId,
            item_id: ItemId,
            updates: Updates,
        ) -> _Response:
            try:
                service = self.infra.with_user(user).with_parent(parent_id).build()
            except DoesNotExistError as e:
                return JSONResponse(RestfulResponse(self.parent).not_found(e), 404)

            try:
                service.update_one(item_id, **updates)
            except DoesNotExistError as e:
                return JSONResponse(self.response.not_found(e), 404)
            except ForbiddenError as e:
                return JSONResponse(self.response.forbidden(e), 403)

            return self.response.ok()

        return endpoint

    def update_many(self, User, Collection) -> Callable[..., _Response]:  # type: ignore
        ParentId = Annotated[str, Path(alias=self.parent_id_alias)]

        def endpoint(user: User, parent_id: ParentId, items: Collection) -> _Response:
            try:
                service = self.infra.with_user(user).with_parent(parent_id).build()
            except DoesNotExistError as e:
                return JSONResponse(RestfulResponse(self.parent).not_found(e), 404)

            try:
                service.update_many(items)
            except DoesNotExistError as e:
                return JSONResponse(self.response.not_found(e), 404)
            except ForbiddenError as e:
                return JSONResponse(self.response.forbidden(e), 403)

            return self.response.ok()

        return endpoint

    def replace_one(self, User, Item) -> Callable[..., _Response]:  # type: ignore
        ParentId = Annotated[str, Path(alias=self.parent_id_alias)]

        def endpoint(user: User, parent_id: ParentId, item: Item) -> _Response:
            try:
                service = self.infra.with_user(user).with_parent(parent_id).build()
            except DoesNotExistError as e:
                return JSONResponse(RestfulResponse(self.parent).not_found(e), 404)

            try:
                service.replace_one(item)
            except DoesNotExistError as e:
                return JSONResponse(self.response.not_found(e), 404)
            except ForbiddenError as e:
                return JSONResponse(self.response.forbidden(e), 403)

            return self.response.ok()

        return endpoint

    def replace_many(self, User, Collection) -> Callable[..., _Response]:  # type: ignore
        ParentId = Annotated[str, Path(alias=self.parent_id_alias)]

        def endpoint(user: User, parent_id: ParentId, items: Collection) -> _Response:
            try:
                service = self.infra.with_user(user).with_parent(parent_id).build()
            except DoesNotExistError as e:
                return JSONResponse(RestfulResponse(self.parent).not_found(e), 404)

            try:
                service.replace_many(items)
            except DoesNotExistError as e:
                return JSONResponse(self.response.not_found(e), 404)
            except ForbiddenError as e:
                return JSONResponse(self.response.forbidden(e), 403)

            return self.response.ok()

        return endpoint

    def delete_one(self, User, ItemId) -> Callable[..., _Response]:  # type: ignore
        ParentId = Annotated[str, Path(alias=self.parent_id_alias)]

        def endpoint(user: User, parent_id: ParentId, item_id: ItemId) -> _Response:
            try:
                service = self.infra.with_user(user).with_parent(parent_id).build()
            except DoesNotExistError as e:
                return JSONResponse(RestfulResponse(self.parent).not_found(e), 404)

            try:
                service.delete_one(item_id)
            except DoesNotExistError as e:
                return JSONResponse(self.response.not_found(e), 404)
            except ForbiddenError as e:
                return JSONResponse(self.response.forbidden(e), 403)

            return self.response.ok()

        return endpoint


@dataclass
class RestfulRootResource:
    name: RestfulName
    infra: RestfulServiceBuilder

    @cached_property
    def response(self) -> RestfulResponse:
        return RestfulResponse(name=self.name)

    def create_one(self, User, Item) -> Callable[..., _Response]:  # type: ignore
        def endpoint(user: User, item: Item) -> _Response:
            service = self.infra.with_user(user).build()

            try:
                item = service.create_one(item)
            except ExistsError as e:
                return JSONResponse(self.response.exists(e), 409)
            except ForbiddenError as e:
                return JSONResponse(self.response.forbidden(e), 403)

            return self.response.created_one(item)

        return endpoint

    def create_many(self, User, Collection) -> Callable[..., _Response]:  # type: ignore
        def endpoint(user: User, items: Collection) -> _Response:
            service = self.infra.with_user(user).build()

            try:
                return self.response.created_many(service.create_many(items))
            except ExistsError as e:
                return JSONResponse(self.response.exists(e), 409)
            except ForbiddenError as e:
                return JSONResponse(self.response.forbidden(e), 403)

        return endpoint

    def read_one(self, User, ItemId) -> Callable[..., _Response]:  # type: ignore
        def endpoint(user: User, item_id: ItemId) -> _Response:
            service = self.infra.with_user(user).build()

            try:
                return self.response.found_one(service.read_one(item_id))
            except DoesNotExistError as e:
                return JSONResponse(self.response.not_found(e), 404)
            except ForbiddenError as e:
                return JSONResponse(self.response.forbidden(e), 403)

        return endpoint

    def read_all(self, User) -> Callable[..., _Response]:  # type: ignore
        def endpoint(user: User) -> _Response:
            service = self.infra.with_user(user).build()

            try:
                return self.response.found_many(list(service.read_all()))
            except ForbiddenError as e:
                return JSONResponse(self.response.forbidden(e), 403)

        return endpoint

    def update_one(self, User, ItemId, Updates) -> Callable[..., _Response]:  # type: ignore
        def endpoint(user: User, item_id: ItemId, updates: Updates) -> _Response:
            service = self.infra.with_user(user).build()

            try:
                service.update_one(item_id, **updates)
            except DoesNotExistError as e:
                return JSONResponse(self.response.not_found(e), 404)
            except ForbiddenError as e:
                return JSONResponse(self.response.forbidden(e), 403)

            return self.response.ok()

        return endpoint

    def update_many(self, User, Collection) -> Callable[..., _Response]:  # type: ignore
        def endpoint(user: User, items: Collection) -> _Response:
            service = self.infra.with_user(user).build()

            try:
                service.update_many(items)
            except DoesNotExistError as e:
                return JSONResponse(self.response.not_found(e), 404)
            except ForbiddenError as e:
                return JSONResponse(self.response.forbidden(e), 403)

            return self.response.ok()

        return endpoint

    def replace_one(self, User, Item) -> Callable[..., _Response]:  # type: ignore
        def endpoint(user: User, item: Item) -> _Response:
            service = self.infra.with_user(user).build()

            try:
                service.replace_one(item)
            except DoesNotExistError as e:
                return JSONResponse(self.response.not_found(e), 404)
            except ForbiddenError as e:
                return JSONResponse(self.response.forbidden(e), 403)

            return self.response.ok()

        return endpoint

    def replace_many(self, User, Collection) -> Callable[..., _Response]:  # type: ignore
        def endpoint(user: User, items: Collection) -> _Response:
            service = self.infra.with_user(user).build()

            try:
                service.replace_many(items)
            except DoesNotExistError as e:
                return JSONResponse(self.response.not_found(e), 404)
            except ForbiddenError as e:
                return JSONResponse(self.response.forbidden(e), 403)

            return self.response.ok()

        return endpoint

    def delete_one(self, User, ItemId) -> Callable[..., _Response]:  # type: ignore
        def endpoint(user: User, item_id: ItemId) -> _Response:
            service = self.infra.with_user(user).build()

            try:
                service.delete_one(item_id)
            except DoesNotExistError as e:
                return JSONResponse(self.response.not_found(e), 404)
            except ForbiddenError as e:
                return JSONResponse(self.response.forbidden(e), 403)

            return self.response.ok()

        return endpoint

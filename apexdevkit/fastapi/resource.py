import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Union

from pydantic import BaseModel
from starlette.responses import JSONResponse

from apexdevkit.error import DoesNotExistError, ExistsError, ForbiddenError
from apexdevkit.fastapi.response import RestfulResponse
from apexdevkit.query.query import (
    Aggregation,
    AggregationOption,
    DateValue,
    Filter,
    FooterOptions,
    Leaf,
    ListValue,
    NullValue,
    NumericValue,
    Operation,
    Operator,
    Page,
    QueryOptions,
    Sort,
    StringValue,
)

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

    def filter_with(self, Service, QueryOptions) -> _Endpoint:  # type: ignore
        def endpoint(service: Service, options: QueryOptions) -> _Response:
            try:
                return self.response.found_many(list(service.filter_with(options)))
            except ForbiddenError as e:
                return JSONResponse(self.response.forbidden(e), 403)

        return endpoint

    def aggregation_with(self, Service, FilterOptions) -> _Endpoint:  # type: ignore
        def endpoint(service: Service, options: FilterOptions) -> _Response:
            try:
                return {
                    "status": "success",
                    "code": 200,
                    "aggregations": service.aggregation_with(options),
                }
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


@dataclass
class _ColumnName:
    raw: str

    def __str__(self) -> str:
        return re.sub(r"(?<!^)(?=[A-Z])", "_", self.raw).lower()


class _NumericItem(BaseModel):
    value: int
    exponent: int

    def to_value(self) -> NumericValue:
        return NumericValue(self.value, self.exponent)


class _StringItem(BaseModel):
    value: str

    def to_value(self) -> StringValue:
        return StringValue(self.value)


class _DateItem(BaseModel):
    date: str

    def to_value(self) -> DateValue:
        return DateValue(self.date)


class _ListItem(BaseModel):
    values: list[_NumericItem | _StringItem | _DateItem]

    def to_value(self) -> ListValue:
        return ListValue([item.to_value() for item in self.values])


class _LeafItem(BaseModel):
    name: str
    values: list[_NumericItem | _StringItem | _DateItem]

    def to_value(self) -> Leaf:
        return Leaf(
            name=str(_ColumnName(self.name)),
            values=[item.to_value() for item in self.values],
        )


class _OperatorItem(BaseModel):
    operation: Operation
    operands: list[Union["_LeafItem", "_OperatorItem"]]

    def to_value(self) -> Operator:
        return Operator(self.operation, [item.to_value() for item in self.operands])


class _SortItem(BaseModel):
    name: str
    is_descending: bool

    def to_value(self) -> Sort:
        return Sort(str(_ColumnName(self.name)), self.is_descending)


class _PageItem(BaseModel):
    page: int | None
    length: int | None
    offset: int | None

    def to_value(self) -> Page:
        return Page(self.page, self.length, self.offset)


class _FilterItem(BaseModel):
    args: list[_NumericItem | _StringItem | _DateItem | _ListItem | None]

    def to_value(self) -> Filter:
        return Filter(
            [arg.to_value() if arg is not None else None for arg in self.args]
        )


class _AggregationOptionItem(BaseModel):
    name: str | None
    aggregation: Aggregation

    def to_value(self) -> AggregationOption:
        return AggregationOption(
            str(_ColumnName(self.name)) if self.name else None,
            self.aggregation,
        )


class _FooterOptions(BaseModel):
    filter: _FilterItem | None
    condition: _OperatorItem | None
    aggregations: list[_AggregationOptionItem]

    def to_footer_options(self) -> FooterOptions:
        return FooterOptions(
            filter=self.filter.to_value() if self.filter else None,
            condition=self.condition.to_value() if self.condition else None,
            aggregations=[item.to_value() for item in self.aggregations],
        )


class _QueryOptions(BaseModel):
    filter: _FilterItem | None
    condition: _OperatorItem | None
    ordering: list[_SortItem]
    paging: _PageItem

    def to_query_options(self) -> QueryOptions:
        return QueryOptions(
            filter=self.filter.to_value() if self.filter else None,
            condition=self.condition.to_value() if self.condition else None,
            ordering=[item.to_value() for item in self.ordering],
            paging=self.paging.to_value(),
        )


class _SummaryItem(BaseModel):
    name: str | None
    aggregation: Aggregation
    result: NumericValue | StringValue | DateValue | NullValue


class _SummaryListEnvelope(BaseModel):
    count: int
    summaries: list[_SummaryItem]


class SummaryResponse(BaseModel):
    status: str
    code: int
    data: _SummaryListEnvelope


class SumResponse(BaseModel):
    status: str
    code: int
    count: int

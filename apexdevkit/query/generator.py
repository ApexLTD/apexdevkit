from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, ClassVar, Generic, Iterable, Protocol, TypeVar

from apexdevkit.error import ForbiddenError
from apexdevkit.query.query import (
    AggregationOption,
    Filter,
    FooterOptions,
    Leaf,
    Operation,
    Operator,
    Page,
    QueryOptions,
    Sort,
    StringValue,
    Summary,
    SummaryExtractor,
)
from apexdevkit.repository import Database, DatabaseCommand

ItemT = TypeVar("ItemT", covariant=True)


class _Loader(Protocol[ItemT]):
    def load(self, raw: dict[str, Any]) -> ItemT:
        pass


@dataclass
class DefaultMsSqlFilter(Generic[ItemT]):
    _database: Database = field(init=False)
    _query_builder: MsSqlQueryBuilder = field(init=False)
    _options: QueryOptions = field(init=False)
    _formatter: _Loader[ItemT] = field(init=False)

    def with_database(self, value: Database) -> DefaultMsSqlFilter[ItemT]:
        self._database = value

        return self

    def with_query_builder(self, value: MsSqlQueryBuilder) -> DefaultMsSqlFilter[ItemT]:
        self._query_builder = value

        return self

    def with_options(self, value: QueryOptions) -> DefaultMsSqlFilter[ItemT]:
        self._options = value

        return self

    def with_formatter(self, value: _Loader[ItemT]) -> DefaultMsSqlFilter[ItemT]:
        self._formatter = value

        return self

    def retrieve(self) -> Iterable[ItemT]:
        if not any(sort.name == "id" for sort in self._options.ordering):
            self._options.ordering.append(Sort("id", False))

        result = self._database.execute(
            self._query_builder.filter(self._options)
        ).fetch_all()

        yield from [self._formatter.load(raw) for raw in result]


@dataclass
class DefaultMsSqlAggregate:
    _database: Database = field(init=False)
    _query_builder: MsSqlQueryBuilder = field(init=False)
    _options: FooterOptions = field(init=False)

    def with_database(self, value: Database) -> DefaultMsSqlAggregate:
        self._database = value

        return self

    def with_query_builder(self, value: MsSqlQueryBuilder) -> DefaultMsSqlAggregate:
        self._query_builder = value

        return self

    def with_options(self, value: FooterOptions) -> DefaultMsSqlAggregate:
        self._options = value

        return self

    def retrieve(self) -> Iterable[Summary]:
        result = self._database.execute(
            self._query_builder.aggregate(self._options)
        ).fetch_one()

        return [
            SummaryExtractor(aggregation).with_value(value)
            for aggregation in self._options.aggregations
            for value in [
                result[
                    f"{aggregation.name if aggregation.name else 'general'}"
                    f"_{aggregation.aggregation.value.lower()}"
                ]
            ]
        ]


class SqlGenerator(Protocol):
    def generate(self) -> str:
        pass


@dataclass
class ConstantSqlGenerator:
    value: str

    def generate(self) -> str:
        return self.value


@dataclass
class NoSqlGenerator(ConstantSqlGenerator):
    value: str = ""


@dataclass
class MsSqlQuery:
    user: SqlGenerator
    selection: SqlGenerator
    filter: SqlGenerator

    condition: SqlGenerator = field(default_factory=NoSqlGenerator)
    ordering: SqlGenerator = field(default_factory=NoSqlGenerator)
    paging: SqlGenerator = field(default_factory=NoSqlGenerator)

    def generate(self) -> DatabaseCommand:
        return DatabaseCommand(f"""
            {self.user.generate()}
            {self.selection.generate()}
            {self.filter.generate()}
            {self.condition.generate()}
            {self.ordering.generate()}
            {self.paging.generate()}
        """)


@dataclass
class MsSqlQueryBuilder:
    source: str = field(init=False)
    username: str = field(init=False)
    translations: dict[str, str] = field(init=False)

    def with_source(self, value: str) -> MsSqlQueryBuilder:
        self.source = value

        return self

    def with_username(self, value: str) -> MsSqlQueryBuilder:
        self.username = value

        return self

    def with_translations(self, value: dict[str, str]) -> MsSqlQueryBuilder:
        self.translations = value

        return self

    def aggregate(self, footer: FooterOptions) -> DatabaseCommand:
        return MsSqlQuery(
            user=MsSqlUserGenerator(self.username),
            selection=MsSqlFooterGenerator(footer.aggregations, self.translations),
            filter=MsSqlSourceGenerator(self.source, footer.filter),
            condition=MsSqlConditionGenerator(footer.condition, self.translations),
        ).generate()

    def filter(self, options: QueryOptions) -> DatabaseCommand:
        return MsSqlQuery(
            user=MsSqlUserGenerator(self.username),
            selection=MsSqlSelectionGenerator(self.translations),
            filter=MsSqlSourceGenerator(self.source, options.filter),
            condition=MsSqlConditionGenerator(options.condition, self.translations),
            ordering=MsSqlOrderGenerator(options.ordering, self.translations),
            paging=MsSqlPagingGenerator(options.paging),
        ).generate()


@dataclass
class MsSqlUserGenerator:
    username: str

    def generate(self) -> str:
        return f"EXECUTE AS USER = '{self.username}'"


@dataclass
class MsSqlSelectionGenerator:
    translations: dict[str, str]

    def generate(self) -> str:
        fields = ", ".join(
            [
                f"[{self.translations[key]}] AS [{key}]"
                for key in self.translations.keys()
            ]
        )

        return f"SELECT {fields}"


@dataclass
class MsSqlFooterGenerator:
    aggregations: list[AggregationOption]
    translations: dict[str, str]

    def generate(self) -> str:
        self._validate()
        fields = ", ".join(
            [
                f"{footer.aggregation.value}"
                f"({self.translations[footer.name] if footer.name else '*'}) AS "
                f"{footer.name if footer.name else 'general'}"
                f"_{footer.aggregation.value.lower()}"
                for footer in self.aggregations
            ]
        )

        return f"SELECT {fields}"

    def _validate(self) -> None:
        if self.translations.keys():
            for footer in self.aggregations:
                if footer.name and footer.name not in self.translations.keys():
                    raise ForbiddenError(message=f"Invalid field name: {footer.name}")


@dataclass
class MsSqlSourceGenerator:
    source: str
    filter: Filter | None = None

    def generate(self) -> str:
        return f"FROM {self.source}{self._argument_list()}"

    def _argument_list(self) -> str:
        if self.filter is None:
            return ""

        return (
            "("
            + ",".join(
                arg.as_arg() if arg is not None else "null" for arg in self.filter.args
            )
            + ")"
        )


@dataclass
class MsSqlConditionGenerator:
    condition: Operator | None
    translations: dict[str, str]

    def generate(self) -> str:
        if self.condition is None:
            return ""
        self._validate(self.condition)

        return f"WHERE ({self._traverse(self.condition)})"

    def _traverse(self, node: Operator) -> str:
        match node.operation:
            case Operation.NOT:
                assert len(node.operands) == 1
                assert isinstance(node.operands[0], Operator)

                return f"NOT ({self._traverse(node.operands[0])})"
            case Operation.AND | Operation.OR:
                assert len(node.operands) > 1

                return f" {node.operation.value} ".join(
                    [f"({self._traverse(operand)})" for operand in node.operands]  # type: ignore
                )
            case _:
                assert len(node.operands) == 1

                return OperationEvaluator(
                    node.operation, self.translations
                ).evaluate_for(
                    node.operands[0],  # type: ignore
                )

    def _validate(self, condition: Operator | None) -> None:
        if condition is not None and self.translations:
            for operand in condition.operands:
                if isinstance(operand, Operator):
                    self._validate(operand)
                else:
                    if operand.name not in self.translations.keys():
                        raise ForbiddenError(
                            message=f"Invalid field name: {operand.name}"
                        )


@dataclass
class MsSqlOrderGenerator:
    ordering: list[Sort]
    translations: dict[str, str]

    def generate(self) -> str:
        if not self.ordering:
            return ""
        self._validate()

        order_clause = ", ".join(
            f"{self.translations[item.name]} DESC"
            if item.is_descending
            else self.translations[item.name]
            for item in self.ordering
        )

        return f"ORDER BY {order_clause}"

    def _validate(self) -> None:
        if self.translations.keys():
            for order in self.ordering:
                if order.name not in self.translations.keys():
                    raise ForbiddenError(message=f"Invalid field name: {order.name}")


@dataclass
class MsSqlPagingGenerator:
    paging: Page

    def generate(self) -> str:
        length = self.paging.length or 200
        offset = self.paging.offset or 0
        page = self.paging.page or 1

        offset = (page - 1) * length + offset

        return f"OFFSET {offset} ROWS FETCH NEXT {length} ROWS ONLY"


@dataclass
class OperationEvaluator:
    operation: Operation
    translations: dict[str, str]

    _TEMPLATES: ClassVar[dict[Operation, str]] = defaultdict(
        lambda: "[{column}] {operation} {a}",
        {
            Operation.BETWEEN: "[{column}] BETWEEN {a} AND {b}",
            Operation.RANGE: "[{column}] >= {a} AND [{column}] < {b}",
            Operation.NULL: "([{column}]) IS NULL",
            Operation.BLANK: "(([{column}]) IS NULL) OR (LEN([{column}]) = 0)",
            Operation.IN: "[{column}] IN ({values})",
            Operation.CONTAINS: "[{column}] LIKE N'%{raw_a}%'",
            Operation.LIKE: "[{column}] LIKE N'{raw_a}'",
            Operation.BEGINS: "[{column}] LIKE N'{raw_a}%'",
            Operation.ENDS: "[{column}] LIKE N'%{raw_a}'",
        },
    )

    def evaluate_for(self, node: Leaf) -> str:
        return self._TEMPLATES[self.operation].format(
            operation=self.operation.value,
            column=self.translations[node.name],
            raw_a=self._get_raw_value(node),
            a=self._get_value(node, 0),
            b=self._get_value(node, 1),
            values=", ".join(val.eval() for val in node.values),
        )

    def _get_raw_value(self, node: Leaf) -> str | None:
        raw_a = self._get_value(node, 0)
        return (
            raw_a[2:-1] if raw_a and isinstance(node.values[0], StringValue) else raw_a
        )

    def _get_value(self, node: Leaf, index: int) -> str | None:
        return node.values[index].eval() if len(node.values) > index else None

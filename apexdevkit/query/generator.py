from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import ClassVar, Protocol

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
)
from apexdevkit.repository import DatabaseCommand


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
        if self.filter is not None:
            return (
                "("
                + ",".join(
                    arg.as_arg() if arg is not None else "null"
                    for arg in self.filter.args
                )
                + ")"
            )
        else:
            return ""


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

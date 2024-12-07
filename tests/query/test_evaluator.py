import pytest
from pytest import fixture

from apexdevkit.error import ForbiddenError
from apexdevkit.query import Leaf, NumericValue, Operation, StringValue
from apexdevkit.query.generator import OperationEvaluator, MsSqlField
from apexdevkit.testing.fake import FakeLeaf, FakeNumericValue, FakeStringValue


@fixture
def num_a() -> NumericValue:
    return FakeNumericValue().entity()


@fixture
def num_b() -> NumericValue:
    return FakeNumericValue().entity()


@fixture
def num_leaf(num_a: NumericValue, num_b: NumericValue) -> Leaf:
    return FakeLeaf(values=[num_a, num_b]).entity()


@fixture
def str_a() -> StringValue:
    return FakeStringValue().entity()


@fixture
def str_b() -> StringValue:
    return FakeStringValue().entity()


@fixture
def str_leaf(str_a: StringValue, str_b: StringValue) -> Leaf:
    return FakeLeaf(values=[str_a, str_b]).entity()


def test_should_not_evaluate_unknown_field() -> None:
    evaluator = OperationEvaluator(Operation.BETWEEN, fields=[])

    with pytest.raises(ForbiddenError):
        evaluator.evaluate_for(FakeLeaf().entity())


def test_should_evaluate_for_between(
    num_a: NumericValue,
    num_b: NumericValue,
    num_leaf: Leaf,
) -> None:
    fields = [MsSqlField("name", alias=num_leaf.name)]
    evaluator = OperationEvaluator(Operation.BETWEEN, fields=fields)

    assert (
        evaluator.evaluate_for(num_leaf)
        == f"[name] BETWEEN {num_a.eval()} AND {num_b.eval()}"
    )


def test_should_evaluate_for_range(
    num_a: NumericValue,
    num_b: NumericValue,
    num_leaf: Leaf,
) -> None:
    fields = [MsSqlField("name", alias=num_leaf.name)]
    evaluator = OperationEvaluator(Operation.RANGE, fields=fields)

    assert (
        evaluator.evaluate_for(num_leaf)
        == f"[name] >= {num_a.eval()} AND [name] < {num_b.eval()}"
    )


def test_should_evaluate_for_null(num_leaf: Leaf) -> None:
    fields = [MsSqlField("name", alias=num_leaf.name)]
    evaluator = OperationEvaluator(Operation.NULL, fields=fields)

    assert evaluator.evaluate_for(num_leaf) == "([name]) IS NULL"


def test_should_evaluate_for_blank(num_leaf: Leaf) -> None:
    fields = [MsSqlField("name", alias=num_leaf.name)]
    evaluator = OperationEvaluator(Operation.BLANK, fields=fields)

    assert evaluator.evaluate_for(num_leaf) == "(([name]) IS NULL) OR (LEN([name]) = 0)"


def test_should_evaluate_for_in(
    num_a: NumericValue,
    num_b: NumericValue,
    num_leaf: Leaf,
) -> None:
    fields = [MsSqlField("name", alias=num_leaf.name)]
    evaluator = OperationEvaluator(Operation.IN, fields=fields)

    assert (
        evaluator.evaluate_for(num_leaf)
        == f"[name] IN ({num_a.eval()}, {num_b.eval()})"
    )


def test_should_evaluate_for_contains(str_a: StringValue, str_leaf: Leaf) -> None:
    fields = [MsSqlField("name", alias=str_leaf.name)]
    evaluator = OperationEvaluator(Operation.CONTAINS, fields=fields)

    assert evaluator.evaluate_for(str_leaf) == f"[name] LIKE N'%{str_a.value}%'"


def test_should_evaluate_for_like(str_a: StringValue, str_leaf: Leaf) -> None:
    fields = [MsSqlField("name", alias=str_leaf.name)]
    evaluator = OperationEvaluator(Operation.LIKE, fields=fields)

    assert evaluator.evaluate_for(str_leaf) == f"[name] LIKE N'{str_a.value}'"


def test_should_evaluate_for_begins(str_a: StringValue, str_leaf: Leaf) -> None:
    fields = [MsSqlField("name", alias=str_leaf.name)]
    evaluator = OperationEvaluator(Operation.BEGINS, fields=fields)

    assert evaluator.evaluate_for(str_leaf) == f"[name] LIKE N'{str_a.value}%'"


def test_should_evaluate_for_ends(str_a: StringValue, str_leaf: Leaf) -> None:
    fields = [MsSqlField("name", alias=str_leaf.name)]
    evaluator = OperationEvaluator(Operation.ENDS, fields=fields)

    assert evaluator.evaluate_for(str_leaf) == f"[name] LIKE N'%{str_a.value}'"


def test_should_evaluate_for_equals(num_a: NumericValue, num_leaf: Leaf) -> None:
    fields = [MsSqlField("name", alias=num_leaf.name)]
    evaluator = OperationEvaluator(Operation.EQUALS, fields=fields)

    assert evaluator.evaluate_for(num_leaf) == f"[name] = {num_a.eval()}"


def test_should_evaluate_for_not_equals(num_a: NumericValue, num_leaf: Leaf) -> None:
    fields = [MsSqlField("name", alias=num_leaf.name)]
    evaluator = OperationEvaluator(Operation.NOT_EQUALS, fields=fields)

    assert evaluator.evaluate_for(num_leaf) == f"[name] <> {num_a.eval()}"


def test_should_evaluate_for_greater(num_a: NumericValue, num_leaf: Leaf) -> None:
    fields = [MsSqlField("name", alias=num_leaf.name)]
    evaluator = OperationEvaluator(Operation.GREATER, fields=fields)

    assert evaluator.evaluate_for(num_leaf) == f"[name] > {num_a.eval()}"


def test_should_evaluate_for_greater_or_equals(
    num_a: NumericValue,
    num_leaf: Leaf,
) -> None:
    fields = [MsSqlField("name", alias=num_leaf.name)]
    evaluator = OperationEvaluator(Operation.GREATER_OR_EQUALS, fields=fields)

    assert evaluator.evaluate_for(num_leaf) == f"[name] >= {num_a.eval()}"


def test_should_evaluate_for_less(num_a: NumericValue, num_leaf: Leaf) -> None:
    fields = [MsSqlField("name", alias=num_leaf.name)]
    evaluator = OperationEvaluator(Operation.LESS, fields=fields)

    assert evaluator.evaluate_for(num_leaf) == f"[name] < {num_a.eval()}"


def test_should_evaluate_for_less_or_equals(
    num_a: NumericValue,
    num_leaf: Leaf,
) -> None:
    fields = [MsSqlField("name", alias=num_leaf.name)]
    evaluator = OperationEvaluator(Operation.LESS_OR_EQUALS, fields=fields)

    assert evaluator.evaluate_for(num_leaf) == f"[name] <= {num_a.eval()}"

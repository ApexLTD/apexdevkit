from apexdevkit.query import Operation, Operator
from apexdevkit.query.generator import (
    MsSqlConditionGenerator,
    OperationEvaluator,
    MsSqlField,
)
from apexdevkit.testing.fake import FakeLeaf, FakeOperator


def test_should_not_apply_condition() -> None:
    assert MsSqlConditionGenerator(None, []).generate() == ""


def test_should_apply_single_condition() -> None:
    leaf = FakeLeaf().entity()
    operator = FakeOperator(operands=[leaf]).entity(operation=Operation.NULL)
    fields = [MsSqlField("name", alias=leaf.name)]

    statement = OperationEvaluator(operator.operation, fields).evaluate_for(leaf)
    assert (
        MsSqlConditionGenerator(operator, fields).generate() == f"WHERE ({statement})"
    )


def test_should_apply_nested_condition() -> None:
    nested_leaf_1 = FakeLeaf().entity()
    nested_operator_1 = FakeOperator(operands=[nested_leaf_1]).entity(
        operation=Operation.NULL
    )

    nested_leaf_2 = FakeLeaf().entity()
    nested_operator_2 = FakeOperator(operands=[nested_leaf_2]).entity(
        operation=Operation.NULL
    )
    fields = [
        MsSqlField("name_1", alias=nested_leaf_1.name),
        MsSqlField("name_2", alias=nested_leaf_2.name),
    ]

    operator = FakeOperator(operands=[nested_operator_1, nested_operator_2]).entity(
        operation=Operation.AND
    )

    statement_1 = OperationEvaluator(nested_operator_1.operation, fields).evaluate_for(
        nested_leaf_1
    )
    statement_2 = OperationEvaluator(nested_operator_2.operation, fields).evaluate_for(
        nested_leaf_2
    )

    assert (
        MsSqlConditionGenerator(operator, fields).generate()
        == f"WHERE (({statement_1}) {operator.operation.value} ({statement_2}))"
    )


def test_should_apply_unary_operation() -> None:
    leaf = FakeLeaf().entity()
    operation = Operator(Operation.NOT, [Operator(Operation.NULL, [leaf])])
    fields = [MsSqlField("name", alias=leaf.name)]

    assert (
        MsSqlConditionGenerator(operation, fields).generate()
        == "WHERE (NOT (([name]) IS NULL))"
    )

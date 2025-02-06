from decimal import Decimal

from apexdevkit.value import Value


def test_should_cast_to_decimal() -> None:
    quantity = Value(1516, 100)

    decimal = quantity.as_decimal()

    assert decimal == Decimal(1516) / Decimal(100)


def test_should_cast_from_string() -> None:
    decimal = "15.16"

    quantity = Value.from_string(decimal)

    assert quantity == Value(1516, 100)


def test_should_add() -> None:
    quantity = Value(1515, 100)
    operand = Value(10, 1000)

    result = quantity.add(operand)

    assert result == Value(1516, 100)


def test_should_subtract() -> None:
    quantity = Value(1517, 100)
    operand = Value(10, 1000)

    result = quantity.subtract(operand)

    assert result == Value(1516, 100)


def test_should_multiply() -> None:
    quantity = Value(15, 100)
    operand = Value(100, 1000)

    result = quantity.multiply(operand)

    assert result == Value(15, 1000)


def test_should_divide() -> None:
    quantity = Value(150, 100)
    operand = Value(5, 10)

    result = quantity.divide(operand)

    assert result == Value(3, 1)


def test_should_convert_to_float() -> None:
    assert float(Value(1516, 100)) == 15.16

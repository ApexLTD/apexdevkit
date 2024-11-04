from decimal import Decimal

from apexdevkit.value import Value


def test_should_cast_to_decimal() -> None:
    value = Value(1516, 100, "GEL")

    decimal = value.as_decimal()

    assert decimal == Decimal(1516) / Decimal(100)


def test_should_cast_from_string() -> None:
    decimal = "15.16"

    value = Value.from_string(decimal)

    assert value == Value(1516, 100)


def test_should_add() -> None:
    value = Value(1515, 100, "GEL")
    operand = Value(10, 1000, "GEL")

    result = value.add(operand)

    assert result == Value(1516, 100, "GEL")


def test_should_subtract() -> None:
    value = Value(1517, 100, "GEL")
    operand = Value(10, 1000, "GEL")

    result = value.subtract(operand)

    assert result == Value(1516, 100, "GEL")

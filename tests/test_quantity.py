from decimal import Decimal

from apexdevkit.value import Quantity


def test_should_cast_to_decimal() -> None:
    quantity = Quantity(1516, 100)

    decimal = quantity.as_decimal()

    assert decimal == Decimal(1516) / Decimal(100)


def test_should_cast_from_string() -> None:
    decimal = "15.16"

    quantity = Quantity.from_string(decimal)

    assert quantity == Quantity(1516, 100)


def test_should_add() -> None:
    quantity = Quantity(1515, 100)
    operand = Quantity(10, 1000)

    result = quantity.add(operand)

    assert result == Quantity(1516, 100)


def test_should_subtract() -> None:
    quantity = Quantity(1517, 100)
    operand = Quantity(10, 1000)

    result = quantity.subtract(operand)

    assert result == Quantity(1516, 100)

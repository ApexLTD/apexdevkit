from decimal import Decimal

from pypebbles.amount import Amount


def test_should_cast_to_decimal() -> None:
    quantity = Amount(1516, 100)

    decimal = quantity.as_decimal()

    assert decimal == Decimal(1516) / Decimal(100)


def test_should_cast_from_string() -> None:
    decimal = "15.16"

    quantity = Amount.parse(decimal)

    assert quantity == Amount(1516, 100)


def test_should_add() -> None:
    quantity = Amount(1515, 100)
    operand = Amount(10, 1000)

    result = quantity.add(operand)

    assert result == Amount(1516, 100)


def test_should_subtract() -> None:
    quantity = Amount(1517, 100)
    operand = Amount(10, 1000)

    result = quantity.subtract(operand)

    assert result == Amount(1516, 100)


def test_should_multiply() -> None:
    quantity = Amount(15, 100)
    operand = Amount(100, 1000)

    result = quantity.multiply(operand)

    assert result == Amount(15, 1000)


def test_should_divide() -> None:
    quantity = Amount(150, 100)
    operand = Amount(5, 10)

    result = quantity.divide(operand)

    assert result == Amount(3, 1)


def test_should_convert_to_float() -> None:
    assert float(Amount(1516, 100)) == 15.16


def test_should_compare_to_decimal() -> None:
    decimal_string = "15.16"

    assert Amount.parse(decimal_string) == Decimal(decimal_string)
    assert Amount.parse(decimal_string) != Decimal(decimal_string) * 2 + 1

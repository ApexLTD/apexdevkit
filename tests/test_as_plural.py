from apexdevkit.fastapi.name import as_plural


def test_ending_with_s() -> None:
    assert as_plural("gas") == "gases"
    assert as_plural("glass") == "glasses"
    assert as_plural("class") == "classes"


def test_ending_with_f() -> None:
    assert as_plural("wolf") == "wolves"


def test_ending_with_x() -> None:
    assert as_plural("box") == "boxes"


def test_ending_with_y() -> None:
    assert as_plural("baby") == "babies"
    assert as_plural("category") == "categories"


def test_ending_with_z() -> None:
    assert as_plural("buzz") == "buzzes"


def test_ending_with_ch() -> None:
    assert as_plural("church") == "churches"
    assert as_plural("branch") == "branches"


def test_ending_with_sh() -> None:
    assert as_plural("dish") == "dishes"


def test_ending_with_fe() -> None:
    assert as_plural("life") == "lives"


def test_ending_with_unknown() -> None:
    assert as_plural("cat") == "cats"
    assert as_plural("unit") == "units"
    assert as_plural("product") == "products"

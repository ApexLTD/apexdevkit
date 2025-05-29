from zoneinfo import ZoneInfo

from apexdevkit.date import DateTime


def test_should_create_from_date_time() -> None:
    date_time = DateTime.from_date_time("2024-05-29T21:27:05", ZoneInfo("Asia/Tbilisi"))
    assert date_time.timestamp_ms == 1717003625000


def test_should_create_from_date() -> None:
    date_time = DateTime.from_date("2024-05-29", ZoneInfo("Asia/Tbilisi"))
    assert date_time.timestamp_ms == 1716926400000


def test_should_create_from_timestamp() -> None:
    date_time = DateTime.from_timestamp(1717003625)
    assert date_time.timestamp_ms == 1717003625000


def test_should_create_from_timestamp_ms() -> None:
    date_time = DateTime.from_timestamp_ms(1717003625000)
    assert date_time.timestamp_ms == 1717003625000


def test_should_create_date_time() -> None:
    date_time = DateTime(1717003625000)
    assert date_time.as_date_time(ZoneInfo("Asia/Tbilisi")) == "2024-05-29T21:27:05"


def test_should_create_date() -> None:
    date_time = DateTime(1717003625000)
    assert date_time.as_date(ZoneInfo("Asia/Tbilisi")) == "2024-05-29"


def test_should_create_timestamp() -> None:
    date_time = DateTime(1717003625000)
    assert date_time.as_timestamp() == 1717003625


def test_should_create_timestamp_ms() -> None:
    date_time = DateTime(1717003625000)
    assert date_time.as_timestamp_ms() == 1717003625000

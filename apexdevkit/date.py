from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class DateTime:
    timestamp_ms: int

    # Date in format of "yyyy-mm-dd"
    def as_date(self, time_zone: ZoneInfo | None = None) -> str:
        if time_zone is None:
            time_zone = ZoneInfo("UTC")

        dt = datetime.fromtimestamp(self.as_timestamp(), tz=UTC)
        local_dt = dt.astimezone(time_zone)
        return local_dt.strftime("%Y-%m-%d")

    # Date in format of "yyyy-mm-ddTHH:MM:SS"
    def as_date_time(self, time_zone: ZoneInfo | None = None) -> str:
        if time_zone is None:
            time_zone = ZoneInfo("UTC")

        dt = datetime.fromtimestamp(self.as_timestamp(), tz=UTC)
        local_dt = dt.astimezone(time_zone)
        return local_dt.strftime("%Y-%m-%dT%H:%M:%S")

    def as_timestamp(self) -> float:
        return float(self.timestamp_ms) / 1000.0

    def as_timestamp_ms(self) -> int:
        return self.timestamp_ms

    # Date in format of "yyyy-mm-dd"
    @classmethod
    def from_date(cls, date: str, time_zone: ZoneInfo | None = None) -> DateTime:
        if time_zone is None:
            time_zone = ZoneInfo("UTC")

        try:
            dt = datetime.strptime(date, "%Y-%m-%d")
            dt = dt.replace(tzinfo=time_zone)
            timestamp_ms = int(dt.timestamp() * 1000)
            return cls(timestamp_ms=timestamp_ms)

        except ValueError as e:
            raise ValueError(
                f"Invalid date format: '{date}'. Expected 'yyyy-mm-dd'."
            ) from e

    # Date in format of "yyyy-mm-ddTHH:MM:SS"
    @classmethod
    def from_date_time(
        cls, date_time: str, time_zone: ZoneInfo | None = None
    ) -> DateTime:
        if time_zone is None:
            time_zone = ZoneInfo("UTC")

        try:
            dt = datetime.strptime(date_time, "%Y-%m-%dT%H:%M:%S")
            dt = dt.replace(tzinfo=time_zone)
            timestamp_ms = int(dt.timestamp() * 1000)
            return cls(timestamp_ms=timestamp_ms)
        except ValueError as e:
            raise ValueError(
                f"Invalid datetime format: '{date_time}'."
                f" Expected 'yyyy-mm-ddTHH:MM:SS'."
            ) from e

    @classmethod
    def from_timestamp(cls, timestamp: float) -> DateTime:
        timestamp_ms = int(timestamp * 1000)
        return cls(timestamp_ms=timestamp_ms)

    @classmethod
    def from_timestamp_ms(cls, timestamp_ms: int) -> DateTime:
        return cls(timestamp_ms=timestamp_ms)

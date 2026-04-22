from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from pycodex.tasks import TaskResult


class Reporter(Protocol):
    def report(self, **results: TaskResult) -> int:
        pass


@dataclass(frozen=True)
class DefaultReporter:
    device: _Device

    @classmethod
    def using(cls, device: _Device) -> DefaultReporter:
        return cls(device)

    def silenced(self) -> _Silenced:
        return _Silenced(self)

    def report(self, **results: TaskResult) -> int:
        return sum(
            self.report_one(name.capitalize(), result)
            for name, result in results.items()
        )

    def report_one(self, name: str, result: TaskResult) -> int:
        if result:
            self.device.with_green().echo(f"✅ {name} passed!")
        else:
            self.device.with_red().echo(f"❌ {name} failed!")

        self.device.with_white().echo(result.stdout)
        self.device.with_yellow().echo(result.stderr)

        return result.exit_code


class _Device(Protocol):
    def with_green(self) -> _Device:
        pass

    def with_red(self) -> _Device:
        pass

    def with_white(self) -> _Device:
        pass

    def with_yellow(self) -> _Device:
        pass

    def echo(self, message: str) -> _Device:
        pass


@dataclass(frozen=True)
class _Silenced:
    reporter: Reporter

    def when(self, silenced: bool) -> Reporter:
        return self.reporter if not silenced else DefaultReporter.using(_NoDevice())


@dataclass(frozen=True)
class _NoDevice:
    def with_green(self) -> _Device:
        return self

    def with_red(self) -> _Device:
        return self

    def with_white(self) -> _Device:
        return self

    def with_yellow(self) -> _Device:
        return self

    def echo(self, message: str) -> _Device:
        _ = message  # suppresses IDE warning for unused argument

        return self

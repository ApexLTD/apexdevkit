from __future__ import annotations

from dataclasses import dataclass
from subprocess import CompletedProcess
from typing import Any


@dataclass(frozen=True, kw_only=True)
class TaskResult:
    stdout: str
    stderr: str
    exit_code: int

    def __bool__(self) -> bool:
        return self.exit_code == 0

    @classmethod
    def parse(cls, result: CompletedProcess[Any]) -> TaskResult:
        return cls(
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
        )

    @classmethod
    def success(cls, *, stdout: str = "", stderr: str = "") -> TaskResult:
        return cls(stdout=stdout, stderr=stderr, exit_code=0)

    @classmethod
    def fail(cls, *, stdout: str = "", stderr: str = "") -> TaskResult:
        return cls(stdout=stdout, stderr=stderr, exit_code=1)

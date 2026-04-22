from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Any

import tomlkit

from pycodex.tasks.result import TaskResult


def _mypy_config() -> dict[str, Any]:
    return {
        "strict": True,
        "ignore_missing_imports": True,
        "show_error_codes": True,
        "pretty": True,
    }


def _ruff_config() -> dict[str, Any]:
    return {
        "lint": {
            "select": [
                "A",
                "ARG",
                "B",
                "C4",
                "PT",
                "RSE",
                "RET",
                "SIM",
                "T20",
                "E",
                "W",
                "F",
                "I",
                "N",
                "UP",
            ],
            "mccabe": {"max-complexity": 10},
        }
    }


def _coverage_config() -> dict[str, Any]:
    return {
        "run": {
            "branch": True,
        },
        "report": {
            "skip_empty": True,
            "skip_covered": True,
            "show_missing": True,
        },
    }


STANDARDS = {
    "tool": {
        "mypy": _mypy_config(),
        "ruff": _ruff_config(),
        "coverage": _coverage_config(),
    }
}


@dataclass(frozen=True)
class SyncToml:
    of: Path

    dry_run: bool = False

    @cached_property
    def _toml(self) -> Path:
        return self.of / "pyproject.toml"

    def run(self) -> TaskResult:
        if not self._toml.exists():
            return TaskResult.fail(stderr=f"{self._toml.name} not found.")

        document = tomlkit.parse(self._toml.read_text(encoding="utf-8"))

        # Create a copy for comparison if dry-run
        original = tomlkit.dumps(document)
        deep_merge(STANDARDS, document)
        modified = tomlkit.dumps(document)

        if original == modified:
            return TaskResult.success(stdout="Configuration is already up to date.")

        if self.dry_run:
            return TaskResult.success(stdout=f"Changes would be applied:\n{modified}")

        self._toml.write_text(modified, encoding="utf-8", newline="\n")

        return TaskResult.success(stdout="Configuration synchronized successfully.")


def deep_merge(source: dict[str, Any], destination: dict[str, Any]) -> None:
    """Recursively merges the source into destination with TOML formatting."""
    for key, value in source.items():
        if isinstance(value, dict):
            # Create a table if the key doesn't exist
            if key not in destination:
                destination[key] = tomlkit.table()
            deep_merge(value, destination[key])
        elif isinstance(value, list):
            # Create a multiline array
            new_array = tomlkit.array()
            for item in value:
                new_array.append(item)
            new_array.multiline(True)
            destination[key] = new_array
        else:
            destination[key] = value

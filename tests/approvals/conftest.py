from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from approvaltests import verify
from approvaltests.core.namer import Namer

from apexdevkit.repository import DatabaseCommand


@pytest.fixture(scope="module")
def approver(module: str) -> Approver:
    return Approver(module)


@pytest.fixture(scope="module")
def module(request: pytest.FixtureRequest) -> str:
    module_path = Path(request.module.__file__)
    module_name = module_path.stem.removeprefix("test_")
    parent_name = module_path.parent.stem

    if parent_name == "approvals":
        return module_name

    return f"{parent_name}/{module_name}"


@dataclass(frozen=True)
class Approver:
    module: str

    def verify_db_command(self, name: str, command: DatabaseCommand) -> None:
        self.verify_sql(name, command.value)
        assert isinstance(command.payload, dict)
        self.verify_json(name, command.payload)

    def verify_sql(self, name: str, code: str) -> None:
        verify(
            "\n".join([line for line in code.split("\n") if line]).strip(),
            namer=_Namer(type="sql", module=self.module, case=name),
        )

    def verify_json(self, name: str, value: Mapping[str, Any]) -> None:
        verify(
            json.dumps(value, indent=2),
            namer=_Namer(type="json", module=self.module, case=name),
        )


@dataclass(frozen=True)
class _Namer(Namer):
    type: str
    module: str
    case: str

    directory: str = "approved"

    @property
    def approvals(self) -> Path:
        return Path(__file__).parent / self.directory / self.module

    def get_received_filename(self, _: str | None = None) -> str:
        return str(self.approvals / f"{self.case}_actual.{self.type}")

    def get_approved_filename(self, _: str | None = None) -> str:
        return str(self.approvals / f"{self.case}.{self.type}")

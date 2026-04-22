from dataclasses import dataclass
from pathlib import Path

from pycodex.reporters import Reporter
from pycodex.tasks import RunMypy, RunRuffCheck, SyncToml
from pycodex.tasks.shell import RunPoetryCheck


@dataclass(frozen=True)
class PyCodex:
    target: Path
    reporter: Reporter

    def sync(self, dry_run: bool = False) -> int:
        return self.reporter.report(
            sync=SyncToml(of=self.target, dry_run=dry_run).run()
        )

    def lint(self) -> int:
        return self.reporter.report(
            poetry=RunPoetryCheck(on=self.target).run(),
            ruff=RunRuffCheck(on=self.target).run(),
            mypy=RunMypy(on=self.target).run(),
        )

    def fix(self, unsafe: bool = False) -> int:
        return self.reporter.report(
            ruff=RunRuffCheck(on=self.target, fix=True, unsafe=unsafe).run()
        )

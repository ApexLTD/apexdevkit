from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import typer

from pycodex.reporters import DefaultReporter
from pycodex.service import PyCodex

cli = typer.Typer(add_completion=False)


@cli.command(
    name="lint",
    help="Run linting (Ruff) and type checking (MyPy).",
)
def _(
    path: str = typer.Option(
        ".",
        "--path",
        "-p",
        help="Target directory.",
    ),
    silent: bool = typer.Option(
        False,
        "--silent",
        "-s",
        help="Suppress output.",
    ),
) -> None:
    raise typer.Exit(
        PyCodex(
            target=Path(path),
            reporter=DefaultReporter.using(TyperDevice()).silenced().when(silent),
        ).lint()
    )


@cli.command(
    name="fix",
    help="Automatically fix Ruff linting errors.",
)
def _(
    path: str = typer.Option(
        ".",
        "--path",
        "-p",
        help="Target directory.",
    ),
    silent: bool = typer.Option(
        False,
        "--silent",
        "-s",
        help="Suppress output.",
    ),
    unsafe: bool = typer.Option(
        False,
        "--unsafe",
        help="Run unsafe Ruff fixes.",
    ),
) -> None:
    raise typer.Exit(
        PyCodex(
            target=Path(path),
            reporter=DefaultReporter.using(TyperDevice()).silenced().when(silent),
        ).fix(unsafe=unsafe)
    )


@cli.command(
    name="sync",
    help="Inject pycodex standards into pyproject TOML file.",
)
def _(
    path: str = typer.Option(
        ".",
        "--path",
        "-p",
        help="Target directory.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show changes without applying them.",
    ),
) -> None:
    raise typer.Exit(
        PyCodex(
            target=Path(path),
            reporter=DefaultReporter.using(TyperDevice()),
        ).sync(dry_run=dry_run)
    )


@dataclass(frozen=True)
class TyperDevice:
    color: str = typer.colors.RESET

    def with_green(self) -> TyperDevice:
        return TyperDevice(typer.colors.GREEN)

    def with_red(self) -> TyperDevice:
        return TyperDevice(typer.colors.RED)

    def with_white(self) -> TyperDevice:
        return TyperDevice(typer.colors.WHITE)

    def with_yellow(self) -> TyperDevice:
        return TyperDevice(typer.colors.YELLOW)

    def echo(self, message: str) -> TyperDevice:
        if message.strip():
            typer.secho(message, fg=self.color)

        return self


if __name__ == "__main__":
    cli()

from __future__ import annotations

import logging.config
from dataclasses import dataclass, field
from typing import Any, Callable

import sentry_sdk
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI

from apexdevkit.environment import environment_variable


def _do_nothing() -> None:
    pass


@dataclass
class UvicornServer:
    logging_config: dict[str, Any]

    host: str = "0.0.0.0"
    port: int = 8000
    path: str = ""

    startup_handlers: list[Callable[[], None]] = field(default_factory=list)

    @classmethod
    def from_env(cls, path: str = ".env") -> UvicornServer:
        load_dotenv(path)
        Sentry().setup()

        return cls(LoggingConfig().setup().as_dict())

    def with_host(self, value: str) -> UvicornServer:
        self.host = value

        return self

    def and_port(self, value: int | str) -> UvicornServer:
        self.port = int(value)

        return self

    def on_path(self, value: str) -> UvicornServer:
        self.path = value

        return self

    def before_run(self, execute: Callable[[], None]) -> UvicornServer:
        self.startup_handlers.append(execute)

        return self

    def run(self, api: FastAPI) -> None:
        self.on_startup()

        uvicorn.run(
            api,
            host=self.host,
            port=self.port,
            root_path=self.path,
            log_config=self.logging_config,
        )

    def on_startup(self) -> None:
        for handler in self.startup_handlers:
            handler()


@dataclass
class Sentry:
    dsn: str = environment_variable("SENTRY_DSN", default="")
    release: str = environment_variable("RELEASE", default="unknown")

    def setup(self) -> None:
        if not self.dsn:
            return

        sentry_sdk.init(
            release=self.release,
            traces_sample_rate=1.0,
            profiles_sample_rate=1.0,
        )


@dataclass
class LoggingConfig:
    level: str = environment_variable("LOGGING_LEVEL", default=str(logging.INFO))

    def setup(self) -> LoggingConfig:
        logging.config.dictConfig(self.as_dict())

        return self

    def as_dict(self) -> dict[str, Any]:
        return {
            "version": 1,
            "disable_existing_loggers": True,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "standard",
                    "level": int(self.level),
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "formatter": "standard",
                    "level": int(self.level),
                    "filename": "app.log",
                    "maxBytes": 1024 * 1024,
                    "backupCount": 10,
                },
            },
            "loggers": {
                "": {
                    "handlers": ["console", "file"],
                    "level": int(self.level),
                    "propagate": False,
                },
                "uvicorn": {
                    "handlers": ["console", "file"],
                    "level": int(self.level),
                    "propagate": False,
                },
            },
        }

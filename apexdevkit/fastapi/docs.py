from typing import TypeVar

from pydantic import BaseModel

PayloadT = TypeVar("PayloadT")


class Response[PayloadT](BaseModel):
    status: str
    code: int
    data: PayloadT


class NoData(BaseModel):
    pass

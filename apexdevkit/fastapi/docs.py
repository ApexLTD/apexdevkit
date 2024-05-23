from typing import Generic, TypeVar

from pydantic import BaseModel

PayloadT = TypeVar("PayloadT")


class Response(BaseModel, Generic[PayloadT]):
    status: str
    code: int
    data: PayloadT


class NoData(BaseModel):
    pass

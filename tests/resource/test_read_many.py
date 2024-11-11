from typing import Annotated

from fastapi import FastAPI
from fastapi.params import Query
from pydantic import BaseModel
from starlette.testclient import TestClient

app = FastAPI()


class AccountFilter(BaseModel):
    debit: int | None = None
    credit: int | None = None


@app.get("/accounts")
def read_many(account_filter: Annotated[AccountFilter, Query()]):
    return {p: v for p, v in account_filter if v}


def test_read_many() -> None:
    http = TestClient(app)

    response = http.get("/accounts", params={"debit": 1})

    assert response.json() == {"debit": 1}

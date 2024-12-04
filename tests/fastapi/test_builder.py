from typing import Any

from starlette.testclient import TestClient

from apexdevkit.fastapi import FastApiBuilder

_MOUNTED_RESPONSE = {"hello": "world"}

mounted_app = FastApiBuilder().build()


@mounted_app.get("/hello")
def mounted_endpoint() -> dict[str, Any]:
    return _MOUNTED_RESPONSE


def test_should_mount() -> None:
    app = FastApiBuilder().with_mounted(mounted=mounted_app).build()

    response = TestClient(app).get("/mounted/hello")

    assert response.status_code == 200
    assert response.json() == _MOUNTED_RESPONSE


def test_should_use_dashes_instead_of_underscores() -> None:
    app = FastApiBuilder().with_mounted(mounted_app=mounted_app).build()

    response = TestClient(app).get("/mounted-app/hello")

    assert response.status_code == 200
    assert response.json() == _MOUNTED_RESPONSE

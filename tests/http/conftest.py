from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def vcr_cassette_dir(request: pytest.FixtureRequest) -> str:
    module_path = Path(request.module.__file__)
    module_name = module_path.stem.removeprefix("test_")

    return str(module_path.parent / "cassettes" / module_name)


@pytest.fixture
def default_cassette_name(request: pytest.FixtureRequest) -> str:
    return str(request.node.name).removeprefix("test_").removeprefix("should_")

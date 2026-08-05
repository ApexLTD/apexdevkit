import pytest
from pathlib import Path


@pytest.fixture(scope="module")
def vcr_cassette_dir(request):
    module_path = Path(request.module.__file__)
    module_name = module_path.stem.removeprefix("test_")

    return str(module_path.parent / "cassettes" / module_name)


@pytest.fixture
def default_cassette_name(request):
    raw = str(request.node.name)
    raw = raw.removeprefix("test_")
    cassette_name = raw.removeprefix("should_")

    return cassette_name

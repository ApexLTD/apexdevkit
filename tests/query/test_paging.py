from apexdevkit.query.generator import MsSqlPagingGenerator
from apexdevkit.testing.fake import FakePage


def test_should_generate_paging() -> None:
    paging = FakePage().entity()

    offset = ((paging.page or 1) - 1) * (paging.length or 200) + (paging.offset or 0)
    assert (
        MsSqlPagingGenerator(paging).generate() == f"OFFSET {offset}"
        f" ROWS FETCH NEXT {(paging.length if paging.length else 200)} ROWS ONLY"
    )

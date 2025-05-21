import os

from apexdevkit.id import ApexID


def test_should_generate_unique() -> None:
    ids_set = set()
    for _ in range(ApexID._sequence_bitmask):
        generated_id = ApexID.id()

        assert generated_id not in ids_set

        ids_set.add(generated_id)


def test_should_encode_sequence_id() -> None:
    assert ApexID.id() & ApexID._sequence_bitmask == ApexID.sequence


def test_should_encode_metadata() -> None:
    os.environ["APEX_ID_METADATA"] = "1000"

    assert ApexID.id() >> 10 & ApexID._metadata_bitmask == 1000


def test_should_encode_timestamp() -> None:
    assert ApexID.id() >> 22 & ApexID._timestamp_bitmask == ApexID.last_timestamp


def test_should_sort_in_generated_order() -> None:
    ids = []

    for _ in range(10_000):
        ids.append(ApexID.id())

    sorted_ids = ids.copy()
    sorted_ids.sort()

    assert ids == sorted_ids

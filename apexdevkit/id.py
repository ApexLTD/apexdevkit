import os
from threading import Lock
from time import time


class ApexID:
    last_timestamp: int = -1
    sequence: int = 0
    lock: Lock = Lock()

    _metadata_bitmask: int = 0x0FFF
    _sequence_bitmask: int = 0x03FF
    _timestamp_bitmask: int = 0x03FFFFFFFFFF

    @classmethod
    def id(cls) -> int:
        """
        Generates a unique identifier with the following structure
        from most significant to least significant:
        1 bit reserved
        41 bits for unix timestamp (millisecond precision)
        12 bits for metadata
        10 bits for sequence
        """
        with cls.lock:
            current_timestamp = cls._get_timestamp()
            if cls.last_timestamp == current_timestamp:
                cls.sequence += 1
            else:
                cls.sequence = 0

            if cls.sequence > cls._sequence_bitmask:
                raise DuplicateIDError("Duplicate ID Generated")

            cls.last_timestamp = current_timestamp

        return (
            (0 << 63)
            | ((cls.last_timestamp & cls._timestamp_bitmask) << 22)
            | ((cls._metadata() & cls._metadata_bitmask) << 10)
            | (cls.sequence & cls._sequence_bitmask)
        )

    @classmethod
    def _get_timestamp(cls) -> int:
        return int(time() * 1000)

    @classmethod
    def _metadata(cls) -> int:
        return int(os.getenv("APEX_ID_METADATA", "0"))


class DuplicateIDError(Exception):
    pass

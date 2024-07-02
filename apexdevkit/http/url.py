from dataclasses import dataclass


@dataclass(frozen=True)
class HttpUrl:
    value: str

    def __add__(self, endpoint: str) -> str:
        return (self.value.strip("/") + "/" + endpoint.strip("/")).strip("/")

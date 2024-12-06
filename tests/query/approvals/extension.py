from approvaltests import verify
from approvaltests.core import Options


def verify_sql(code: str) -> None:
    verify(
        "\n".join([line if line.strip() else "" for line in code.split("\n")]),
        options=Options({"extension_with_dot": ".sql"}),
    )

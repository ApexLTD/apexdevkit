from approvaltests import Options, verify


def verify_sql(code: str) -> None:
    verify(code, options=Options({"extension_with_dot": ".sql"}))

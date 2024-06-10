from pathlib import Path
from apm.case.case import get_case_insensitive_path


def test_get_case_insensitive_path() -> None:
    assert get_case_insensitive_path("./Apm") == Path("apm")
    assert get_case_insensitive_path("./tests") == Path("tests")
    assert get_case_insensitive_path("./.aVaLoN") == Path(".avalon")

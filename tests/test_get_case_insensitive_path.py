from apm.case.case import get_case_insensitive_path


def test_get_case_insensitive_path() -> None:
    assert get_case_insensitive_path("./Apm") == "./apm"
    assert get_case_insensitive_path("./tests") == "./tests"
    assert get_case_insensitive_path("./.aVaLoN") == "./.avalon"

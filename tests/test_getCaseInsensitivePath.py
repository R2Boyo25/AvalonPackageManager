from apm.case.case import getCaseInsensitivePath


def test_getCaseInsensitivePath() -> None:
    assert getCaseInsensitivePath("./Apm") == "./apm"
    assert getCaseInsensitivePath("./tests") == "./tests"
    assert getCaseInsensitivePath("./.aVaLoN") == "./.avalon"

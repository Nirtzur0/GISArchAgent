import pytest


pytestmark = [pytest.mark.unit]


def test_guess_artifact_type__fn_pdf__returns_pdf():
    from src.data_management.pydoll_fetcher import _guess_artifact_type

    url = "https://mavat.iplan.gov.il/rest/api/Attacments/?eid=1&fn=abc.pdf"
    assert _guess_artifact_type(url) == "pdf"


def test_guess_artifact_type__fn_kml__returns_kml():
    from src.data_management.pydoll_fetcher import _guess_artifact_type

    url = "https://mavat.iplan.gov.il/rest/api/Attacments/?eid=1&fn=abc.kml"
    assert _guess_artifact_type(url) == "kml"


def test_guess_artifact_type__fn_zip__returns_zip():
    from src.data_management.pydoll_fetcher import _guess_artifact_type

    url = "https://mavat.iplan.gov.il/rest/api/Attacments/?eid=1&fn=abc.zip"
    assert _guess_artifact_type(url) == "zip"


def test_guess_artifact_type__fn_docx__returns_doc():
    from src.data_management.pydoll_fetcher import _guess_artifact_type

    url = "https://mavat.iplan.gov.il/rest/api/Attacments/?eid=1&fn=abc.docx"
    assert _guess_artifact_type(url) == "doc"


def test_guess_artifact_type__unknown__returns_unknown():
    from src.data_management.pydoll_fetcher import _guess_artifact_type

    url = "https://mavat.iplan.gov.il/rest/api/Attacments/?eid=1&fn=abc.bin"
    assert _guess_artifact_type(url) == "unknown"


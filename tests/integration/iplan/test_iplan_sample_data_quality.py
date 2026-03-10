import re

import pytest

from src.infrastructure.factory import ApplicationFactory


pytestmark = [pytest.mark.integration, pytest.mark.db, pytest.mark.iplan]


@pytest.fixture(scope="module")
def vectorstore_path(tmp_path_factory):
    return tmp_path_factory.mktemp("vectorstore")


@pytest.fixture(scope="module")
def repo(vectorstore_path):
    factory = ApplicationFactory(chroma_persist_dir=str(vectorstore_path))
    return factory.get_regulation_repository()


def test_hebrew_search__plan_query__returns_results(repo):
    results = repo.search("תכנית", limit=10)
    assert results


def test_iplan_like_metadata__contains_plan_number_and_municipality(repo):
    results = repo.search("תכנית", limit=25)
    assert results

    with_plan_number = 0
    with_municipality = 0

    for r in results:
        md = r.metadata or {}
        if md.get("plan_number"):
            with_plan_number += 1
        if md.get("municipality") or md.get("municipality_name") or md.get("city"):
            with_municipality += 1

    assert with_plan_number > 0
    assert with_municipality > 0


def test_iplan_like_diversity__multiple_municipalities(repo):
    results = repo.search("תכנית", limit=30)
    municipalities = set()

    for r in results:
        md = r.metadata or {}
        for key in ("municipality", "municipality_name", "city"):
            v = md.get(key)
            if isinstance(v, str) and v.strip():
                municipalities.add(v.strip())

    assert len(municipalities) >= 2


def test_iplan_endpoint_family__plan_number_pattern_on_iplan_sources(repo):
    results = repo.search("תכנית", limit=30)
    assert results

    pattern = re.compile(r"^\d{3}-\d{7}$")
    iplan_like_records = []

    for r in results:
        md = r.metadata or {}
        source = str(md.get("source", "")).lower()
        if "iplan" in source:
            iplan_like_records.append(md)

    assert (
        iplan_like_records
    ), "Expected iPlan-family records in integration sample data."
    assert any(
        isinstance(md.get("plan_number"), str) and pattern.match(md["plan_number"])
        for md in iplan_like_records
    ), "Expected at least one iPlan-family record with canonical plan number pattern NNN-NNNNNNN."

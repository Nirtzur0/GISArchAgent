import pytest

from tests.helpers.factories import FIXED_NOW_UTC, make_iplan_raw_feature


pytestmark = [pytest.mark.unit]


def test_parse_record__valid_feature__produces_searchable_record(monkeypatch):
    # Arrange
    from src.data_pipeline.sources.iplan import source as iplan_source_module
    from src.data_pipeline.sources.iplan.source import IPlanDataSource

    class _FixedDateTime:
        @staticmethod
        def now():
            # Match the module's expectation (naive datetime is also acceptable).
            return FIXED_NOW_UTC.replace(tzinfo=None)

    monkeypatch.setattr(iplan_source_module, "datetime", _FixedDateTime)

    raw = make_iplan_raw_feature(
        objectid=42,
        plan_number="101-0121850",
        plan_name="תכנית 101-0121850",
        municipality_name="ירושלים",
        entity_subtype_desc="תכנית מפורטת",
    )

    # Avoid IPlanDataSource.__init__ (it constructs Selenium dependencies).
    ds = object.__new__(IPlanDataSource)

    # Act
    record = ds.parse_record(raw)

    # Assert
    assert record.id == "iplan_42"
    assert record.title == "תכנית 101-0121850"
    assert "101-0121850" in record.content
    assert "ירושלים" in record.content
    assert record.source == "iPlan GIS"

    assert record.metadata["plan_number"] == "101-0121850"
    assert record.metadata["municipality_name"] == "ירושלים"
    assert record.metadata["source_system"] == "iPlan GIS"

    assert record.fetched_at == FIXED_NOW_UTC.replace(tzinfo=None)

"""Factories/builders for readable test data creation."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from typing import Any

from src.application.dtos import RegulationQuery
from src.data_pipeline.core.interfaces import DataRecord


FIXED_NOW_UTC = datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


def make_regulation_query(
    *,
    query_text: str = "parking requirements",
    location: str | None = "national",
    regulation_type: str | None = None,
    max_results: int = 5,
) -> RegulationQuery:
    return RegulationQuery(
        query_text=query_text,
        location=location,
        regulation_type=regulation_type,
        max_results=max_results,
    )


def make_iplan_raw_feature(
    *,
    objectid: int = 123,
    plan_number: str = "101-0121850",
    plan_name: str = "תכנית לדוגמה",
    entity_subtype_desc: str = "תכנית מפורטת",
    municipality_name: str = "ירושלים",
    plan_targets: str = "יעדים לדוגמה",
    main_details: str = "פרטים לדוגמה",
    status_desc: str = "תכנית שאושרה (מתקדמות)",
    district_name: str = "מחוז ירושלים",
) -> dict[str, Any]:
    # IPlanDataSource.parse_record expects ArcGIS-like feature dict with `attributes`.
    return {
        "attributes": {
            "OBJECTID": objectid,
            "PL_NUMBER": plan_number,
            "PL_NAME": plan_name,
            "ENTITY_SUBTYPE_DESC": entity_subtype_desc,
            "MUNICIPALITY_NAME": municipality_name,
            "PLAN_TARGETS": plan_targets,
            "MAIN_DETAILS": main_details,
            "PL_STATUS_DESC": status_desc,
            "DISTRICT_NAME": district_name,
        }
    }


def make_data_record(
    *,
    record_id: str = "iplan_123",
    title: str = "תכנית לדוגמה",
    content: str = "תכנית מספר: 101-0121850",
    source: str = "iPlan GIS",
    metadata: dict[str, Any] | None = None,
    fetched_at: datetime | None = None,
) -> DataRecord:
    return DataRecord(
        id=record_id,
        title=title,
        content=content,
        source=source,
        metadata=metadata or {"plan_number": "101-0121850"},
        fetched_at=fetched_at or FIXED_NOW_UTC,
    )


def with_data_record_metadata(record: DataRecord, **updates: Any) -> DataRecord:
    md = dict(record.metadata or {})
    md.update(updates)
    return replace(record, metadata=md)


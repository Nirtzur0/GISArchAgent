from src.vectorstore.unified_pipeline import UnifiedDataPipeline


def test_unified_pipeline__document_link_regulation_includes_artifact_type_metadata():
    pipeline = object.__new__(UnifiedDataPipeline)  # avoid heavy __init__ (Chroma/Gemini)

    doc = {
        "url": "https://mavat.iplan.gov.il/rest/api/Attacments/?eid=1&fn=foo.kml",
        "title": "Boundary (KML)",
        "artifact_type": "kml",
    }
    attrs = {
        "OBJECTID": 123,
        "PL_NUMBER": "101-0057273",
        "PL_NAME": "Some Plan",
        "MUNICIPALITY_NAME": "Jerusalem",
    }

    reg = UnifiedDataPipeline._extract_regulation_from_document(pipeline, doc, attrs, mavat_plan_id="1000216487")
    assert reg is not None
    assert reg.metadata.get("artifact_type") == "kml"
    assert "סוג קובץ: kml" in (reg.content or "")


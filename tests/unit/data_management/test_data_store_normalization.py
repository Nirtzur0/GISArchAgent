import json

from src.data_management.data_store import DataStore


def test_load_normalizes_stale_metadata_and_empty_stat_keys(tmp_path):
    data_file = tmp_path / "iplan_layers.json"
    data_file.write_text(
        json.dumps(
            {
                "metadata": {
                    "source": "iPlan ArcGIS REST API (via fetch_webpage tool)",
                    "fetched_at": "2025-12-21T14:24:12.705551",
                    "count_saved": 99,
                },
                "features": [
                    {
                        "attributes": {
                            "pl_number": "308-0083621",
                            "district_name": "חיפה",
                            "plan_county_name": None,
                            "station_desc": None,
                        }
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    store = DataStore(str(data_file))

    metadata = store.get_metadata()
    stats = store.get_statistics()

    assert metadata["source"] == "iPlan ArcGIS REST API"
    assert metadata["last_updated"] == "2025-12-21T14:24:12.705551"
    assert metadata["count_saved"] == 1
    assert stats["by_city"]["Unknown city"] == 1
    assert stats["by_status"]["Unknown status"] == 1

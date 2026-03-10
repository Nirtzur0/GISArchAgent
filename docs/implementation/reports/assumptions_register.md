# Assumptions Register

| Assumption | Impact | Status | Owner | Evidence / Decision Note | Target Stage |
| --- | --- | --- | --- | --- | --- |
| iPlan ArcGIS endpoints remain reachable from contributor environments. | high | open | maintainer | Repo includes live iPlan repository adapter (`src/infrastructure/repositories/iplan_repository.py`), but no guaranteed uptime controls. Artifact citation: `ART-EXT-001`. | Shape |
| Chrome + CDP availability for `pydoll-python` exists where full build pipeline is executed. | medium | open | maintainer | Build tooling expects browser automation (`scripts/build_vectordb_cli.py check`). Artifact citations: `ART-EXT-004`, `ART-EXT-002`. | Shape |
| Local Chroma persistence is adequate for current usage scale. | medium | validated | maintainer | Chroma persistence path + health checks are implemented (`src/infrastructure/repositories/chroma_repository.py`, `scripts/quick_status.py`). Artifact citation: `ART-EXT-005`. | Shape |
| Project can remain useful without configured Gemini keys. | medium | validated | maintainer | Regulation fallback answer path is deterministic (`src/application/services/regulation_query_service.py`). Artifact citation: `ART-EXT-003`. | Shape |
| Existing legacy docs can be reconciled incrementally without large churn. | low | accepted | maintainer | This packet introduces manifest baseline and defers full legacy-doc cleanup to later milestones. | Bet |

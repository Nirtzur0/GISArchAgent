# How-To: Interpret Outputs

## Regulation query outputs
- Source: `RegulationResult` in `src/application/dtos.py`.
- Key fields:
  - `regulations`: matched regulation entities
  - `total_found`: count
  - `answer`: synthesized or fallback summary

Interpretation tips:
- If `answer` references fallback mode, LLM synthesis is not configured.
- Validate relevance by checking regulation titles/types/jurisdiction.

## Plan search outputs
- Source: `PlanSearchResult` and `AnalyzedPlan` DTOs.
- Key fields:
  - `plans`: plan entries with optional vision analysis
  - `execution_time_ms`: runtime indicator

## Data CLI outputs
- `scripts/data_cli.py status`:
  - total plans, district/city/status breakdown.
- `scripts/data_cli.py export`:
  - JSON artifact with metadata + features.

## Validation anchors
- Run marker suites from `docs/manifest/09_runbook.md` command map.
- Use `data_contracts` marker suite for output schema/range checks.

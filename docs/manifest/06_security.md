# Security Baseline

## Security Posture Summary
- The project is local-first and currently optimized for developer/operator usage.
- There is no built-in user authentication/authorization layer in the Streamlit app.
- Primary security controls are configuration hygiene, boundary validation, and safe failure handling.

## Secrets and Configuration
- Local secrets are expected in `.env` (ignored by git).
- `src/config.py` reads settings through `pydantic-settings`.
- Required action: keep production/API keys out of logs and docs.

## Boundary Input Validation
- Query DTOs and repository method signatures constrain expected shape.
- Data contract tests cover required fields, missingness, ranges, and allowed categories.
- Required follow-up: strengthen explicit input normalization at UI boundaries where free text is accepted.

## External Dependency Risks
- iPlan repository currently disables TLS verification in requests session (`verify=False`) for compatibility with government endpoints.
- Risk: increases MITM exposure in hostile networks.
- Mitigation plan:
  - document trusted network assumptions,
  - add optional strict-SSL mode with explicit opt-out,
  - surface warning logs when SSL bypass is active.

## Local Data Handling
- Data and vector artifacts are stored under `data/` and excluded by `.gitignore`.
- Required action: define backup and retention guidance in runbook.

## Reliability and Abuse Controls
- Current rate-limit, retry, and timeout strategy is partial and adapter-specific.
- Required follow-up:
  - normalize timeout/retry policy across external adapters,
  - define idempotency expectations for build operations.

## Security TODOs
- Add explicit redaction policy for logs in `docs/manifest/07_observability.md`.
- Add basic static/security dependency scanning to CI once workflows exist.
- Define minimal threat model for local operator misuse and secret leakage.

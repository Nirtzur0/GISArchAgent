"""
Shared assertion helpers for high-signal contract tests.

These helpers intentionally produce debug-first failure messages:
- what failed
- expected constraint
- observed stats (min/max/missing rate, etc.)
- small samples of offending values
- a context string that names the stage/flow
"""

from __future__ import annotations

from collections import Counter
from math import isnan
from typing import Any, Iterable, Mapping, Sequence


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def _get_field(obj: Any, field: str) -> Any:
    if isinstance(obj, Mapping):
        return obj.get(field)
    return getattr(obj, field, None)


def assert_required_fields(obj: Any, fields: Sequence[str], context: str = "") -> None:
    missing_fields: list[str] = []
    empty_fields: list[str] = []

    for f in fields:
        if isinstance(obj, Mapping):
            if f not in obj:
                missing_fields.append(f)
                continue
            v = obj.get(f)
        else:
            if not hasattr(obj, f):
                missing_fields.append(f)
                continue
            v = getattr(obj, f)

        if _is_missing(v):
            empty_fields.append(f)

    if missing_fields or empty_fields:
        raise AssertionError(
            "Required fields contract failed"
            + (f" (context={context})" if context else "")
            + f"\nmissing_fields={missing_fields}"
            + f"\nempty_fields={empty_fields}"
        )


def assert_missing_rate(
    rows: Sequence[Any],
    field: str,
    max_rate: float,
    context: str = "",
    sample: int = 5,
) -> None:
    if max_rate < 0 or max_rate > 1:
        raise ValueError("max_rate must be in [0, 1]")
    if not rows:
        raise AssertionError(
            "Missingness contract failed"
            + (f" (context={context})" if context else "")
            + "\nrows is empty; cannot compute missing rate"
        )

    missing_idx: list[int] = []
    for i, r in enumerate(rows):
        v = _get_field(r, field)
        if _is_missing(v):
            missing_idx.append(i)

    rate = len(missing_idx) / len(rows)
    if rate > max_rate:
        offenders = missing_idx[:sample]
        offender_values = [(i, _get_field(rows[i], field)) for i in offenders]
        raise AssertionError(
            f"Missingness contract failed for field='{field}'"
            + (f" (context={context})" if context else "")
            + f"\nexpected: missing_rate <= {max_rate:.3f}"
            + f"\nobserved: missing_rate={rate:.3f} ({len(missing_idx)}/{len(rows)})"
            + f"\nexample_offenders(index,value)={offender_values}"
        )


def assert_in_range(
    values: Any,
    min: float | None = None,
    max: float | None = None,
    allow_nan: bool = False,
    context: str = "",
    sample: int = 8,
) -> None:
    if isinstance(values, (str, bytes)):
        raise TypeError("values must be a number or an iterable of numbers")

    if isinstance(values, Iterable) and not isinstance(values, (int, float)):
        seq = list(values)
    else:
        seq = [values]

    bad: list[tuple[int, Any]] = []
    numeric: list[float] = []

    for i, v in enumerate(seq):
        if v is None:
            bad.append((i, v))
            continue
        try:
            fv = float(v)
        except Exception:
            bad.append((i, v))
            continue

        if isnan(fv):
            if allow_nan:
                continue
            bad.append((i, v))
            continue

        numeric.append(fv)
        if min is not None and fv < min:
            bad.append((i, v))
        elif max is not None and fv > max:
            bad.append((i, v))

    if bad:
        observed_min = min(numeric) if numeric else None
        observed_max = max(numeric) if numeric else None
        raise AssertionError(
            "Range contract failed"
            + (f" (context={context})" if context else "")
            + f"\nexpected: min>={min} max<={max} allow_nan={allow_nan}"
            + f"\nobserved: min={observed_min} max={observed_max} n={len(seq)}"
            + f"\nexample_offenders(index,value)={bad[:sample]}"
        )


def assert_allowed_values(
    values: Iterable[Any],
    allowed: set[Any],
    context: str = "",
    sample: int = 8,
) -> None:
    allowed_set = set(allowed)
    counts = Counter(values)
    unexpected = {k: v for k, v in counts.items() if k not in allowed_set}

    if unexpected:
        top = sorted(unexpected.items(), key=lambda kv: kv[1], reverse=True)[:sample]
        raise AssertionError(
            "Allowed-values contract failed"
            + (f" (context={context})" if context else "")
            + f"\nallowed={sorted(allowed_set)}"
            + f"\nunexpected_counts(top)={top}"
        )


def assert_unique(values: Iterable[Any], context: str = "", sample: int = 8) -> None:
    seq = list(values)
    counts = Counter(seq)
    dups = [(k, v) for k, v in counts.items() if v > 1]
    if dups:
        dups = sorted(dups, key=lambda kv: kv[1], reverse=True)[:sample]
        raise AssertionError(
            "Uniqueness contract failed"
            + (f" (context={context})" if context else "")
            + f"\nduplicates(top)={dups}"
        )


def assert_probability_vector(vec: Sequence[float], tol: float = 1e-6, context: str = "") -> None:
    if not vec:
        raise AssertionError(
            "Probability-vector contract failed"
            + (f" (context={context})" if context else "")
            + "\nvector is empty"
        )

    floats = [float(x) for x in vec]
    assert_in_range(floats, min=0.0 - tol, max=1.0 + tol, context=context)

    s = sum(floats)
    if abs(s - 1.0) > tol:
        raise AssertionError(
            "Probability-vector contract failed"
            + (f" (context={context})" if context else "")
            + f"\nexpected: sum~=1.0 (tol={tol})"
            + f"\nobserved: sum={s}"
        )


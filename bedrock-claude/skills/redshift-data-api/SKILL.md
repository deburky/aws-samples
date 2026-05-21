---
name: redshift-data-api
description: Query AWS Redshift via the boto3 Redshift Data API. Use for any Redshift query from Python when direct connections time out or aren't available. Handles execute → poll → paginated fetch → typed DataFrame. TRIGGER when user asks to "query redshift", "pull from redshift", run SQL against Redshift, or when `redshift_connector` connection fails.
---

# Redshift Data API Skill

Use this pattern when you need to run SQL against Redshift from Python, especially when:

- `redshift_connector` connection times out (no VPN, firewall, etc.)
- You want a serverless / credential-less approach via IAM
- You need pagination for large result sets (>100k rows)
- The target is an agentic workflow that must be reproducible

## Required environment variables

```bash
REDSHIFT_REGION     # e.g., eu-west-1
REDSHIFT_HOST       # full hostname — cluster ID is parsed as first dot-segment
REDSHIFT_DB_NAME    # database name
REDSHIFT_USER_NAME  # DbUser for temporary credentials
AWS_PROFILE         # optional — defaults to "renmoney-prod" in the reference script
```

## Reference implementation

See `helper.py` in this skill directory. Import `execute_redshift_query` from it, or copy the function body into your project at e.g. `analysis/<area>/scripts/read_sql.py`.

Basic usage:

```python
from helper import execute_redshift_query
import pandas as pd

rows = execute_redshift_query("SELECT ... FROM schema.table")
df = pd.DataFrame(rows)
```

The function:
1. Starts the statement via `execute_statement`
2. Polls `describe_statement` until `FINISHED` / fails hard on `FAILED`/`ABORTED`
3. Pulls results with `get_statement_result` — **paginated via `NextToken`** (important for >~2k rows)
4. Flattens each cell's type-tagged dict to a plain value; returns `None` for `isNull`

## Pagination — critical

The bare `get_statement_result` call returns only the first page (~2k rows). If you omit `NextToken` handling you silently drop data. The helper's `iter_statement_results` loops until `NextToken` is absent.

## Output formats

- **Small / ad-hoc** (<50k rows): return `list[dict]`, convert to DataFrame in caller
- **Large / persisted**: use `to_parquet` (typed, smaller) — avoid CSV for wide tables with many NULLs

## Type handling

The Data API returns values as `{longValue: ...}`, `{stringValue: ...}`, `{doubleValue: ...}`, or `{isNull: true}`. The helper extracts the first value or returns `None`. Cast numerics explicitly in pandas via `pd.to_numeric(..., errors="coerce")` — some Redshift columns store numbers as strings with literal `'NULL'` / empty strings (common in external schemas like Spectrum).

## Anti-patterns to avoid

- Do NOT use `redshift_connector` for agentic workflows — requires VPN / direct network, inconsistent.
- Do NOT `UNLOAD` to S3 for exploratory pulls; only for large multi-million-row extracts where pagination cost is prohibitive.
- Do NOT rely on SQL-side regex `SIMILAR TO '[0-9]+...'` to guard numeric casts — push cleaning into Python after the pull.
- Do NOT skip `NextToken` pagination "because the first page looks fine" — you will get silently truncated results.

## Invocation checklist

When using this skill:

1. Confirm env vars are set (`echo $REDSHIFT_HOST`); otherwise surface the exact missing var to the user.
2. Write SQL to a file under `analysis/<area>/sql/` — never inline in Python — so it's reviewable/rerunnable.
3. Point the Python script at the SQL file via `Path.read_text()`.
4. Save results under `analysis/<area>/data/` as parquet (default) or Excel only if Risk / business stakeholders need it.
5. Echo row count + output path at the end so the user can verify.

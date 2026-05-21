"""Redshift Data API query executor.

Executes read-only SQL via the Redshift Data API (boto3).
No direct connections, no VPN — works anywhere with IAM credentials.

Required env vars:
    REDSHIFT_REGION, REDSHIFT_HOST, REDSHIFT_DB_NAME, REDSHIFT_USER_NAME
    AWS_PROFILE (optional, defaults to "default")
"""

import os
import time
from typing import Any

import boto3


def execute_query(sql: str) -> tuple[list[str], list[list[Any]]]:
    """Run read-only SQL via Redshift Data API.

    Returns (column_names, rows) where each row is a list of values.
    Raises RuntimeError on query failure.
    """
    rs_region = os.environ["REDSHIFT_REGION"]
    rs_host = os.environ["REDSHIFT_HOST"]
    rs_db = os.environ["REDSHIFT_DB_NAME"]
    rs_db_user = os.environ["REDSHIFT_USER_NAME"]
    rs_cluster = rs_host.split(".")[0] if "." in rs_host else rs_host
    profile = os.environ.get("AWS_PROFILE", "default")

    session = boto3.Session(profile_name=profile, region_name=rs_region)
    client = session.client("redshift-data")

    resp = client.execute_statement(
        ClusterIdentifier=rs_cluster,
        Database=rs_db,
        DbUser=rs_db_user,
        Sql=sql,
    )
    request_id = resp["Id"]

    # Poll until finished
    while True:
        desc = client.describe_statement(Id=request_id)
        status = desc["Status"]
        if status == "FINISHED":
            break
        if status in ("FAILED", "ABORTED"):
            raise RuntimeError(f"Query {status}: {desc.get('Error', 'unknown')}")
        time.sleep(0.5)

    if not desc.get("HasResultSet", False):
        return [], []

    # Paginated fetch
    columns: list[str] = []
    rows: list[list[Any]] = []
    next_token: str | None = None
    while True:
        kwargs: dict[str, Any] = {"Id": request_id}
        if next_token:
            kwargs["NextToken"] = next_token
        result = client.get_statement_result(**kwargs)
        if not columns:
            columns = [col["name"] for col in result["ColumnMetadata"]]
        for record in result.get("Records", []):
            row = []
            for cell in record:
                if "isNull" in cell:
                    row.append(None)
                else:
                    row.append(next(iter(cell.values())))
            rows.append(row)
        next_token = result.get("NextToken")
        if not next_token:
            break

    return columns, rows

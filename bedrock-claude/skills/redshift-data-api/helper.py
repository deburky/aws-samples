"""Reusable Redshift Data API helper with pagination + null handling.

Usage:
    from helper import execute_redshift_query
    rows = execute_redshift_query("SELECT ...")  # returns list[dict]

Env vars required:
    REDSHIFT_REGION, REDSHIFT_HOST, REDSHIFT_DB_NAME, REDSHIFT_USER_NAME
    AWS_PROFILE (optional, defaults to "default")
"""

import os
import sys
import time
from typing import Any, Iterator

import boto3
from botocore.exceptions import ClientError


def _cell_to_value(cell: dict[str, Any]) -> Any:
    """Extract scalar from Redshift Data API type-tagged cell."""
    if not cell or "isNull" in cell:
        return None
    return next(iter(cell.values()))


def _iter_pages(client, request_id: str) -> Iterator[tuple[list[str], list[list[dict]]]]:
    """Yield (columns, records) for each page of a finished statement."""
    next_token: str | None = None
    while True:
        kwargs: dict[str, Any] = {"Id": request_id}
        if next_token:
            kwargs["NextToken"] = next_token
        result = client.get_statement_result(**kwargs)
        columns = [col["name"] for col in result["ColumnMetadata"]]
        yield columns, result.get("Records", [])
        next_token = result.get("NextToken")
        if not next_token:
            return


def execute_redshift_query(sql: str) -> list[dict[str, Any]]:
    """Run SQL via Redshift Data API and return all rows as list of dicts.

    Handles:
      - execute_statement / describe_statement polling
      - NextToken pagination across get_statement_result pages
      - isNull / type-tagged cell flattening

    Fails hard (sys.exit(1)) on missing env vars or query error.
    """
    try:
        rs_region = os.environ["REDSHIFT_REGION"]
        rs_host = os.environ["REDSHIFT_HOST"]
        rs_db = os.environ["REDSHIFT_DB_NAME"]
        rs_db_user = os.environ["REDSHIFT_USER_NAME"]
    except KeyError as e:
        print(f"ERROR: Missing required environment variable: {e}")
        sys.exit(1)

    rs_cluster = rs_host.split(".")[0] if "." in rs_host else rs_host
    profile = os.environ.get("AWS_PROFILE", "default")

    session = boto3.Session(profile_name=profile, region_name=rs_region)
    client = session.client("redshift-data")

    try:
        resp = client.execute_statement(
            ClusterIdentifier=rs_cluster,
            Database=rs_db,
            DbUser=rs_db_user,
            Sql=sql,
        )
    except ClientError as e:
        print(f"ERROR: execute_statement failed: {e}")
        sys.exit(1)

    request_id = resp["Id"]

    while True:
        try:
            desc = client.describe_statement(Id=request_id)
        except ClientError as e:
            print(f"ERROR: describe_statement failed: {e}")
            sys.exit(1)

        status = desc["Status"]
        if status == "FINISHED":
            break
        if status in ("FAILED", "ABORTED"):
            print(f"Query {status}: {desc.get('Error', 'Unknown error')}")
            sys.exit(1)
        time.sleep(0.5)

    if not desc.get("HasResultSet", False):
        return []

    results: list[dict[str, Any]] = []
    columns: list[str] = []
    try:
        for cols, rows in _iter_pages(client, request_id):
            if not columns:
                columns = cols
            for row in rows:
                results.append({c: _cell_to_value(cell) for c, cell in zip(columns, row)})
    except ClientError as e:
        print(f"ERROR: get_statement_result failed: {e}")
        sys.exit(1)

    return results

"""Lambda: an S3 Inventory manifest lands, normalize the listed JSON into an S3 Table.

Triggered by the creation of an inventory ``manifest.json``. The handler reads the
manifest, follows it to the inventory data files (gzipped CSV listing every object
in the source bucket), reads each source JSON, normalizes the batch with dlt, and
appends the flat result to a managed Amazon S3 Table via the Iceberg REST catalog.

dlt owns normalization and schema evolution. No duckdb: dlt writes Parquet to the
function's /tmp, pyarrow reads it, pyiceberg writes it to the S3 Table.
"""

import csv
import glob
import gzip
import io
import json
import os
import shutil
import urllib.parse

import boto3
import dlt
import pyarrow.parquet as pq
from pyiceberg.catalog.rest import RestCatalog

# Lambda's filesystem is read-only except /tmp, so point dlt's state there.
os.environ.setdefault("HOME", "/tmp")
os.environ.setdefault("DLT_DATA_DIR", "/tmp/.dlt")

s3 = boto3.client("s3")
REGION = os.environ.get("AWS_REGION", "us-east-1")
WAREHOUSE = os.environ["S3TABLES_WAREHOUSE"]
NAMESPACE = os.environ.get("S3TABLES_NAMESPACE", "raw")
TABLE = os.environ.get("TARGET_TABLE", "applications")


def _catalog() -> RestCatalog:
    return RestCatalog(
        "s3tables",
        **{
            "uri": f"https://s3tables.{REGION}.amazonaws.com/iceberg",
            "warehouse": WAREHOUSE,
            "rest.sigv4-enabled": "true",
            "rest.signing-name": "s3tables",
            "rest.signing-region": REGION,
            # use pyarrow's S3 FileIO so we don't bundle s3fs/botocore
            "py-io-impl": "pyiceberg.io.pyarrow.PyArrowFileIO",
        },
    )


def _ensure_namespace(catalog: RestCatalog) -> None:
    if (NAMESPACE,) not in catalog.list_namespaces():
        catalog.create_namespace(NAMESPACE)


def _object_keys_from_manifest(bucket: str, manifest_key: str):
    """Read an inventory manifest.json and return (source_bucket, [object keys])."""
    manifest = json.loads(s3.get_object(Bucket=bucket, Key=manifest_key)["Body"].read())
    source_bucket = manifest["sourceBucket"]
    keys: list[str] = []
    for entry in manifest["files"]:  # each is a gzipped CSV of object rows
        raw = s3.get_object(Bucket=bucket, Key=entry["key"])["Body"].read()
        text = gzip.decompress(raw).decode()
        keys.extend(
            urllib.parse.unquote_plus(row[1])
            for row in csv.reader(io.StringIO(text))
        )
    return source_bucket, keys


def _normalize(records: list[dict]):
    """Normalize the batch to local Parquet with dlt; return it as a pyarrow table."""
    shutil.rmtree("/tmp/edp_out", ignore_errors=True)
    pipe = dlt.pipeline(
        pipeline_name="edp",
        destination=dlt.destinations.filesystem(bucket_url="file:///tmp/edp_out"),
        dataset_name="raw",
        pipelines_dir="/tmp/dlt_pipelines",
    )
    pipe.run(
        records, table_name=TABLE, write_disposition="append", loader_file_format="parquet"
    )
    files = glob.glob(f"/tmp/edp_out/raw/{TABLE}/*.parquet")
    tbl = pq.read_table(files)
    return tbl.select([c for c in tbl.schema.names if not c.startswith("_dlt")])


def handler(event, context):
    """Process an S3 inventory manifest event into the target S3 Table."""
    record = event["Records"][0]["s3"]
    bucket = record["bucket"]["name"]
    key = urllib.parse.unquote_plus(record["object"]["key"])
    if not key.endswith("manifest.json"):
        return {"skipped": key}

    source_bucket, keys = _object_keys_from_manifest(bucket, key)
    records = [
        json.loads(s3.get_object(Bucket=source_bucket, Key=k)["Body"].read())
        for k in keys
        if k.startswith("data/") and k.endswith(".json")
    ]
    if not records:
        return {"processed_files": 0}

    tbl = _normalize(records)

    cat = _catalog()
    _ensure_namespace(cat)
    ident = (NAMESPACE, TABLE)
    if cat.table_exists(ident):
        iceberg_table = cat.load_table(ident)
        with iceberg_table.update_schema() as update:  # evolve for any new fields
            update.union_by_name(tbl.schema)
    else:
        iceberg_table = cat.create_table(ident, schema=tbl.schema)
    iceberg_table.append(tbl)

    return {"processed_files": len(records), "table": f"{NAMESPACE}.{TABLE}"}

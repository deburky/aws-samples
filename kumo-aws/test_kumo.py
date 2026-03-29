"""
Basic integration tests for Kumo. This is not meant to be exhaustive, but should cover the basics of each service.
"""

# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "boto3",
#   "boto3-stubs",
#   "docker",
# ]
# ///

import socket
import time

import boto3
import boto3.session
import docker
from botocore.awsrequest import AWSPreparedRequest

# -----------------------------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------------------------
IMAGE = "ghcr.io/sivchari/kumo:latest"
PORT = 4566
ENDPOINT = f"http://localhost:{PORT}"
ENDPOINT_APIGW = f"http://localhost:{PORT}/apigateway"

SESSION = boto3.session.Session(
    region_name="us-east-1",
    aws_access_key_id="test",
    aws_secret_access_key="test",
)


# -----------------------------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------------------------
def wait_for_port(host: str, port: int, timeout: float = 30.0) -> None:
    """Wait until a TCP port is accepting connections."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1):
                return
        except OSError:
            time.sleep(0.5)
    raise TimeoutError(f"Port {port} not ready after {timeout}s")


def _strip_charset(request: AWSPreparedRequest, **kwargs: object) -> None:
    """Strip charset from Content-Type header for Kumo compatibility."""
    # Kumo strict-matches "application/x-www-form-urlencoded" without charset
    ct = request.headers.get("Content-Type", b"")
    if isinstance(ct, bytes):
        ct = ct.decode()
    if "application/x-www-form-urlencoded" in ct:
        request.headers["Content-Type"] = "application/x-www-form-urlencoded"


def start_kumo() -> None:
    """Wait for Kumo to be ready."""
    print(f"Waiting for Kumo on port {PORT} ...")
    wait_for_port("localhost", PORT)
    print("Kumo is up.\n")


# -----------------------------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------------------------
def test_s3() -> None:
    """Test S3 functionality."""
    client = SESSION.client("s3", endpoint_url=ENDPOINT)
    client.create_bucket(Bucket="test-bucket")
    buckets = [b["Name"] for b in client.list_buckets().get("Buckets", [])]
    assert "test-bucket" in buckets
    client.put_object(Bucket="test-bucket", Key="hello.txt", Body=b"hello kumo")
    body = client.get_object(Bucket="test-bucket", Key="hello.txt")["Body"].read()
    assert body == b"hello kumo"
    print("S3 ✓")


def test_sqs() -> None:
    """Test SQS functionality."""
    client = SESSION.client("sqs", endpoint_url=ENDPOINT)
    q = client.create_queue(QueueName="test-queue")
    url = q["QueueUrl"]
    client.send_message(QueueUrl=url, MessageBody="hello kumo")
    resp = client.receive_message(QueueUrl=url)
    messages = resp.get("Messages", [])
    assert messages and messages[0]["Body"] == "hello kumo"
    print("SQS ✓")


def test_dynamodb() -> None:
    """Test DynamoDB functionality."""
    client = SESSION.client("dynamodb", endpoint_url=ENDPOINT)
    client.create_table(
        TableName="test-table",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )
    resource = SESSION.resource("dynamodb", endpoint_url=ENDPOINT)
    table = resource.Table("test-table")
    table.put_item(Item={"id": "1", "value": "hello"})
    item = table.get_item(Key={"id": "1"})["Item"]
    assert item["value"] == "hello"
    print("DynamoDB ✓")


def test_rds() -> None:
    """Test RDS functionality."""
    client = SESSION.client("rds", endpoint_url=ENDPOINT)
    client.meta.events.register("before-send.rds.*", _strip_charset)
    client.create_db_instance(
        DBInstanceIdentifier="test-db",
        DBInstanceClass="db.t3.micro",
        Engine="postgres",
        MasterUsername="admin",
        MasterUserPassword="password123",
        AllocatedStorage=20,
    )
    resp = client.describe_db_instances(DBInstanceIdentifier="test-db")
    db = resp["DBInstances"][0]
    assert db["DBInstanceIdentifier"] == "test-db"
    assert db["Engine"] == "postgres"
    print("RDS ✓")


def test_ecr() -> None:
    """Test ECR functionality."""
    client = SESSION.client("ecr", endpoint_url=ENDPOINT)
    client.create_repository(repositoryName="test-repo")
    repos = client.describe_repositories()["repositories"]
    assert any(r["repositoryName"] == "test-repo" for r in repos)
    print("ECR ✓")


def test_api_gateway() -> None:
    """Test API Gateway functionality."""
    client = SESSION.client("apigateway", endpoint_url=ENDPOINT_APIGW)
    resp = client.create_rest_api(name="test-api")
    assert resp.get("name") == "test-api"
    assert resp.get("id")
    print("API GW ✓")


# -----------------------------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------------------------
def main() -> None:
    """Run all tests."""
    dc = docker.from_env()

    print(f"Pulling {IMAGE} ...")
    dc.images.pull(IMAGE)
    print("Image ready.")

    container = dc.containers.run(
        IMAGE,
        detach=True,
        ports={f"{PORT}/tcp": PORT},
        remove=True,
    )
    print(f"Container started: {container.short_id}")

    try:
        start_kumo()
        test_s3()
        test_sqs()
        test_dynamodb()
        test_rds()
        test_ecr()
        test_api_gateway()

        print("\nAll tests passed.")
    finally:
        print(f"\nStopping container {container.short_id} ...")
        container.stop()
        print("Done.")


if __name__ == "__main__":
    main()

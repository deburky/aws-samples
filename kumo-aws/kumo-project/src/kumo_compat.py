"""
Kumo compatibility helpers for boto3.

Kumo has two quirks compared to LocalStack:
- Query-protocol services (STS, IAM, RDS, ...) fail with MissingTargetHeader
  because Kumo strict-matches 'application/x-www-form-urlencoded' without the
  '; charset=utf-8' suffix that boto3 appends.
- Some services are routed under a path prefix (IAM -> /iam/, API GW -> /apigateway/).

KumoSession wraps boto3.session.Session and handles both transparently.
"""

import os
from typing import Any, cast

import boto3
import boto3.session
from botocore.awsrequest import AWSPreparedRequest

# Services that use the Query protocol and need the charset strip.
_QUERY_PROTOCOL_SERVICES = frozenset({"sts", "iam", "rds", "cloudformation", "sns"})

# Services routed under a non-root path prefix in Kumo.
_PATH_PREFIXES: dict[str, str] = {
    "iam": "/iam",
    "apigateway": "/apigateway",
}


def _strip_charset(request: AWSPreparedRequest, **kwargs: object) -> None:
    """Strip charset suffix from Content-Type for Kumo Query-protocol compatibility."""
    ct = request.headers.get("Content-Type", b"")
    if isinstance(ct, bytes):
        ct = ct.decode()
    if "application/x-www-form-urlencoded" in ct:
        request.headers["Content-Type"] = "application/x-www-form-urlencoded"


class KumoSession:
    """Boto3 session wrapper pre-configured for Kumo.

    Creates clients with the correct endpoint URL (including any Kumo path
    prefix) and registers the charset hook for Query-protocol services.

    Usage::

        session = KumoSession()
        s3 = session.client("s3")
        iam = session.client("iam")   # endpoint and hook applied automatically
        sts = session.client("sts")   # charset hook applied automatically
    """

    def __init__(
        self,
        endpoint_url: str | None = None,
        region_name: str | None = None,
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
    ) -> None:
        """Initialize KumoSession with endpoint URL and AWS credentials."""
        self._base_url: str = (
            endpoint_url if endpoint_url is not None
            else os.getenv("ENDPOINT_URL", "http://localhost:4566")
        )
        self._session = boto3.session.Session(
            region_name=region_name or os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
            aws_access_key_id=aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID", "test"),
            aws_secret_access_key=aws_secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY", "test"),
        )

    def client(self, service_name: str) -> Any:
        """Return a boto3 client with Kumo compatibility applied."""
        prefix = _PATH_PREFIXES.get(service_name, "")
        endpoint_url = self._base_url + prefix
        boto3_client = cast(Any, self._session).client(service_name, endpoint_url=endpoint_url)
        if service_name in _QUERY_PROTOCOL_SERVICES:
            boto3_client.meta.events.register(
                f"before-send.{service_name}.*", _strip_charset
            )
        return boto3_client

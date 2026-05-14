# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "boto3",
# ]
# ///
#
"""
AppConfig Agent - Python implementation.

Encodes the same logic as the Go binary (GoAmzn-AWSAppConfigCachingAgent)
but fetches raw config via the management API (appconfig) so _variants and
rules are always available for local evaluation — including native feature
flag profiles that the Data API returns pre-evaluated without _variants.

  - client.go         : orchestrates fetch + cache + backup
  - runtimes/lambda.go: module-level cache so warm Lambda invocations skip the poll
  - backup.go         : disk backup written on every successful fetch

Intended as a drop-in replacement for the Lambda extension layer / sidecar binary.
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any

import boto3
from botocore.exceptions import ClientError

LOG = logging.getLogger(__name__)

# Module-level cache — survives Lambda warm starts, equivalent to the agent
# process staying alive between invocations.
_CACHE: dict[str, tuple[bytes, float]] = {}

# ID cache — application/profile names don't change, resolve once and keep forever.
_ID_CACHE: dict[str, str] = {}

# Default backup directory, mirrors the agent's /tmp usage on Lambda.
_DEFAULT_BACKUP_DIR = Path(os.environ.get("APPCONFIG_BACKUP_DIR", "/tmp/appconfig"))

# How many seconds before we consider a cached entry stale and re-poll.
_DEFAULT_POLL_INTERVAL = int(os.environ.get("APPCONFIG_POLL_INTERVAL", "45"))


def _config_key(application: str, environment: str, profile: str) -> str:
    """Mirrors appconfigclient/configkey.go — canonical string key for the cache."""
    return f"{application}/{environment}/{profile}"


def _write_backup(key: str, value: bytes, backup_dir: Path) -> None:
    """Mirrors appconfigclient/backup.go."""
    try:
        backup_dir.mkdir(parents=True, exist_ok=True)
        safe_name = key.replace("/", "__")
        path = backup_dir / f"{safe_name}.json"
        path.write_bytes(value)
        LOG.debug("wrote configuration '%s' to %s", key, path)
    except OSError as exc:
        LOG.warning("unable to write backup for '%s': %s", key, exc)


def _read_backup(key: str, backup_dir: Path) -> bytes | None:
    """Mirrors the backup load path in appconfigclient/backup.go."""
    safe_name = key.replace("/", "__")
    path = backup_dir / f"{safe_name}.json"
    if path.exists():
        try:
            data = path.read_bytes()
            LOG.debug("loaded backup for '%s' from %s", key, path)
            return data
        except OSError as exc:
            LOG.warning("unable to load backup for '%s': %s", key, exc)
    return None


class AppConfigClient:
    """
    Python equivalent of the AppConfig Agent binary.

    Usage in a Lambda handler:

        _appconfig = AppConfigClient()

        def handler(event, context):
            config = _appconfig.get_configuration("MyApp", "prod", "my-profile")
            ...

    The instance is created at module level so the in-memory cache survives
    warm invocations, exactly like the agent sidecar process.
    """

    def __init__(
        self,
        region: str | None = None,
        poll_interval: int = _DEFAULT_POLL_INTERVAL,
        backup_dir: Path | None = None,
        boto_session: boto3.Session | None = None,
    ) -> None:
        """Initialize with optional region, polling interval, and backup settings."""
        session = boto_session or boto3.Session()
        self._client = session.client(
            "appconfig",
            region_name=region or os.environ.get("AWS_REGION"),
        )
        self._poll_interval = poll_interval
        self._backup_dir = backup_dir or _DEFAULT_BACKUP_DIR

    def _resolve_id(self, list_method: str, name: str, **kwargs: Any) -> str | None:
        """Resolve a resource name to its AppConfig ID, cached permanently."""
        kwarg_str = ",".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
        cache_key = f"{list_method}/{name}/{kwarg_str}"
        if cache_key in _ID_CACHE:
            return _ID_CACHE[cache_key]
        try:
            response = getattr(self._client, list_method)(**kwargs)
            for item in response.get("Items", []):
                if item.get("Name") == name:
                    _ID_CACHE[cache_key] = item["Id"]
                    return item["Id"]
        except ClientError as exc:
            LOG.error("AppConfig %s failed for '%s': %s", list_method, name, exc)
        return None

    def _fetch(self, application: str, profile: str) -> bytes:
        """Fetch raw config bytes via management API — always includes _variants."""
        app_id = self._resolve_id("list_applications", application)
        if not app_id:
            raise RuntimeError(f"AppConfig application '{application}' not found")

        profile_id = self._resolve_id(
            "list_configuration_profiles", profile, ApplicationId=app_id
        )
        if not profile_id:
            raise RuntimeError(
                f"AppConfig profile '{profile}' not found in '{application}'"
            )

        versions = self._client.list_hosted_configuration_versions(
            ApplicationId=app_id,
            ConfigurationProfileId=profile_id,
            MaxResults=1,
        )
        if not versions.get("Items"):
            raise RuntimeError(f"No versions found for AppConfig profile '{profile}'")

        version_number = versions["Items"][0]["VersionNumber"]
        resp = self._client.get_hosted_configuration_version(
            ApplicationId=app_id,
            ConfigurationProfileId=profile_id,
            VersionNumber=version_number,
        )
        return resp["Content"].read()  # type: ignore[no-any-return]

    def get_configuration(
        self,
        application: str,
        environment: str,
        profile: str,
        as_json: bool = True,
    ) -> Any:
        """
        Fetch a configuration value, using the cache when it is fresh.

        Equivalent to a GET on the agent's local HTTP endpoint:
          http://localhost:2772/applications/{app}/environments/{env}/configurations/{profile}

        Args:
            application: AppConfig application name or ID.
            environment: AppConfig environment name or ID (used for cache key only).
            profile:     Configuration profile name or ID.
            as_json:     Parse bytes as JSON (default). Set False for raw bytes.

        Returns:
            Parsed JSON (default) or raw bytes, depending on as_json.
        """
        key = _config_key(application, environment, profile)
        cached = _CACHE.get(key)
        if cached is not None:
            value, fetched_at = cached
            if time.monotonic() - fetched_at < self._poll_interval:
                LOG.debug("cache hit for '%s'", key)
                return self._decode(value, as_json)

        try:
            value = self._fetch(application, profile)
        except (ClientError, RuntimeError) as exc:
            LOG.warning("fetch failed for '%s', trying backup: %s", key, exc)
            backup = _read_backup(key, self._backup_dir)
            if backup is not None:
                return self._decode(backup, as_json)
            raise

        _CACHE[key] = (value, time.monotonic())
        _write_backup(key, value, self._backup_dir)
        return self._decode(value, as_json)

    @staticmethod
    def _decode(value: bytes, as_json: bool) -> Any:
        return json.loads(value) if as_json else value

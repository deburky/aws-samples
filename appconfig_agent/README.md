# appconfig_agent
A pure-Python, in-process replacement for AWS AppConfig Agent behavior, implemented as a generic package.

This package fetches raw AppConfig content through the management API and evaluates feature-flag variant rules locally. It is designed for cases where you need `_variants` and per-request rule evaluation behavior available in your own runtime.

## Background
The original AppConfig Lambda-extension model runs a Go sidecar that exposes cached configuration over a local HTTP endpoint:

```
GET http://localhost:2772/applications/{app}/environments/{env}/configurations/{profile}
Context: key1=value1&key2=value2
```

This package moves that behavior into Python code inside your process: fetch, cache, fallback backup, and local rule evaluation.

## Why management API instead of data API
The AppConfig Data API (`appconfigdata`) is optimized for session-token polling:
1. `StartConfigurationSession`
2. `GetLatestConfiguration(token)`

For feature-flag profiles, that flow can return pre-evaluated output and may not retain full `_variants` details in the returned payload.

This package uses the AppConfig management API (`appconfig`) flow instead:
1. `ListApplications` (resolve application name → ID)
2. `ListConfigurationProfiles` (resolve profile name → ID)
3. `ListHostedConfigurationVersions` (identify latest version)
4. `GetHostedConfigurationVersion` (fetch raw bytes)

This ensures raw configuration is available for local variant/rule evaluation.

## Trade-offs
- Keeps raw configuration and local rule logic in your app runtime.
- Removes sidecar/Lambda-layer dependency.
- Polling is version-based in this implementation rather than token-based deltas.

## Architecture
### `client.py` (`AppConfigClient`)
- Module-level cache (`_CACHE`) keyed by `application/environment/profile`.
- ID cache (`_ID_CACHE`) for application/profile name-to-ID resolution.
- Disk backup fallback (default `/tmp/appconfig`) on successful fetches.
- Configurable poll interval (default `45` seconds).

### `rule_evaluator.py`
- Parses and evaluates S-expression rules (`and`, `or`, `not`, `eq`, `gt`, `in`, `exists`, `split`, `matches`, etc.).
- Implements deterministic percentage bucketing for `split` using FNV-1a 32-bit hashing.
- `evaluate_config` applies variant matching and promotes selected attributes.
- `extract_attributes` strips AppConfig metadata fields from evaluated flags.

## Public API
`__init__.py` exports:
- `AppConfigClient`
- `evaluate_config`
- `extract_attributes`

## Dependencies
`client.py` includes inline PEP 723 script metadata with:
- `boto3`

If you are using `uv`, this supports script-style dependency resolution directly.  
For package/distribution workflows, define dependencies in `pyproject.toml` as well.

## Required AWS permissions
At minimum:
- `appconfig:ListApplications`
- `appconfig:ListConfigurationProfiles`
- `appconfig:ListHostedConfigurationVersions`
- `appconfig:GetHostedConfigurationVersion`

## Environment variables
- `AWS_REGION` (recommended): region for the AppConfig client.
- `APPCONFIG_POLL_INTERVAL` (optional, default `45`): cache refresh interval in seconds.
- `APPCONFIG_BACKUP_DIR` (optional, default `/tmp/appconfig`): local backup directory.

## Usage
```python
from appconfig_agent import AppConfigClient, evaluate_config, extract_attributes

client = AppConfigClient()
raw = client.get_configuration("my-app", "prod", "feature-flags")

context = {
    "application_loanId": "123456",
    "tier": "pro",
    "country": "US",
}

evaluated = evaluate_config(raw, context)
flag = evaluated.get("my_flag", {})
attrs = extract_attributes(flag)
variant = flag.get("_variant")
```

## Notes
- `environment` is part of the cache key to preserve the agent-style interface.
- On fetch failure, the client attempts to serve the last successful backup from disk.

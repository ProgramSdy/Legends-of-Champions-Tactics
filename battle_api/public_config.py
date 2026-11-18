"""Fail-closed validation for a future Public deployment environment.

The API itself already denies protected operations when storage, identity, or
Origin configuration is missing.  Deployment supervision should run this
module as ``ExecStartPre`` so a misconfigured Public process never reports as
started in the first place.  No secret values are printed.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import ipaddress
import json
import os
from pathlib import Path
from typing import Mapping
from urllib.parse import urlsplit

from .public_db_ops import PublicDatabaseOperationError, inspect_public_database


class PublicConfigurationError(RuntimeError):
    """Public environment is incomplete or unsafe."""


@dataclass(frozen=True)
class PublicConfigurationEvidence:
    release_mode: str
    public_database: str
    public_origin: str
    trusted_proxy_ips: tuple[str, ...]
    hmac_key_version: int
    battle_capacity: int
    provisional_ttl_seconds: int
    inactivity_seconds: int
    public_battles_enabled: bool


def _positive_integer(
    environment: Mapping[str, str], name: str, default: str
) -> int:
    try:
        value = int(environment.get(name, default))
    except ValueError as exc:
        raise PublicConfigurationError(f"{name} must be an integer.") from exc
    if value < 1:
        raise PublicConfigurationError(f"{name} must be positive.")
    return value


def validate_public_configuration(
    environment: Mapping[str, str] | None = None,
) -> PublicConfigurationEvidence:
    env = os.environ if environment is None else environment
    if env.get("LOCT_RELEASE_MODE") != "public":
        raise PublicConfigurationError("LOCT_RELEASE_MODE must be public.")
    database_text = env.get("BATTLE_API_PUBLIC_DB")
    if not database_text:
        raise PublicConfigurationError("BATTLE_API_PUBLIC_DB is required.")
    try:
        database = inspect_public_database(Path(database_text))
    except PublicDatabaseOperationError as exc:
        raise PublicConfigurationError(str(exc)) from exc

    origin = env.get("BATTLE_API_PUBLIC_ORIGIN", "")
    parsed = urlsplit(origin)
    try:
        parsed_port = parsed.port
    except ValueError as exc:
        raise PublicConfigurationError(
            "BATTLE_API_PUBLIC_ORIGIN must be one exact HTTPS origin."
        ) from exc
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise PublicConfigurationError(
            "BATTLE_API_PUBLIC_ORIGIN must be one exact HTTPS origin."
        )
    canonical_origin = f"https://{parsed.hostname}"
    if parsed_port is not None:
        canonical_origin += f":{parsed_port}"
    if origin != canonical_origin:
        raise PublicConfigurationError(
            "BATTLE_API_PUBLIC_ORIGIN must not contain a path or trailing slash."
        )

    hmac_key = env.get("BATTLE_API_PUBLIC_HMAC_KEY", "").encode("utf-8")
    rate_key = env.get("BATTLE_API_RATE_LIMIT_HMAC_KEY", "").encode("utf-8")
    if len(hmac_key) < 32:
        raise PublicConfigurationError(
            "BATTLE_API_PUBLIC_HMAC_KEY must contain at least 32 bytes."
        )
    if len(rate_key) < 32:
        raise PublicConfigurationError(
            "BATTLE_API_RATE_LIMIT_HMAC_KEY must contain at least 32 bytes."
        )
    if hmac_key == rate_key:
        raise PublicConfigurationError(
            "Public identity and rate-limit HMAC keys must be independent."
        )
    key_version = _positive_integer(
        env, "BATTLE_API_PUBLIC_HMAC_KEY_VERSION", "1"
    )

    proxy_values = tuple(
        item.strip()
        for item in env.get("BATTLE_API_TRUSTED_PROXY_IPS", "").split(",")
        if item.strip()
    )
    if not proxy_values:
        raise PublicConfigurationError(
            "BATTLE_API_TRUSTED_PROXY_IPS requires the explicit Nginx peer address."
        )
    try:
        proxies = tuple(str(ipaddress.ip_address(item)) for item in proxy_values)
    except ValueError as exc:
        raise PublicConfigurationError(
            "BATTLE_API_TRUSTED_PROXY_IPS must contain exact IP addresses."
        ) from exc

    battle_gate = env.get("BATTLE_API_ENABLE_PUBLIC_BATTLES", "0")
    if battle_gate not in {"0", "1"}:
        raise PublicConfigurationError(
            "BATTLE_API_ENABLE_PUBLIC_BATTLES must be omitted, 0, or 1."
        )
    return PublicConfigurationEvidence(
        release_mode="public",
        public_database=database.path,
        public_origin=canonical_origin,
        trusted_proxy_ips=proxies,
        hmac_key_version=key_version,
        battle_capacity=_positive_integer(
            env, "BATTLE_API_PUBLIC_BATTLE_CAPACITY", "20"
        ),
        provisional_ttl_seconds=_positive_integer(
            env, "BATTLE_API_PUBLIC_PROVISIONAL_TTL_SECONDS", "120"
        ),
        inactivity_seconds=_positive_integer(
            env, "BATTLE_API_PUBLIC_INACTIVITY_SECONDS", "1800"
        ),
        public_battles_enabled=battle_gate == "1",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate Public deployment configuration without printing secrets."
    )
    parser.parse_args()
    try:
        evidence = validate_public_configuration()
    except PublicConfigurationError as exc:
        parser.error(str(exc))
    print(json.dumps(asdict(evidence), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

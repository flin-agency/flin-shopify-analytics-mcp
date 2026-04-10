"""Configuration parsing for MCP server."""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from typing import Mapping


DEFAULT_API_VERSION = "2026-04"
DEFAULT_OAUTH_REFRESH_SKEW_SECONDS = 60
DEFAULT_OAUTH_TOKEN_TTL_FALLBACK_SECONDS = 86399


@dataclass(frozen=True)
class Config:
    store_domain: str
    api_version: str
    auth_mode: str
    static_access_token: str | None
    client_id: str | None
    client_secret: str | None
    oauth_refresh_skew_seconds: int
    oauth_token_ttl_fallback_seconds: int
    ca_bundle_path: str | None


def _require_value(source: Mapping[str, str], key: str) -> str:
    value = source.get(key)
    if value is None or not str(value).strip():
        raise ValueError(f"Missing required environment variable: {key}")
    return str(value).strip()


def _optional_value(source: Mapping[str, str], key: str) -> str | None:
    value = source.get(key)
    if value is None:
        return None
    trimmed = str(value).strip()
    return trimmed or None


def _normalize_store_domain(raw_domain: str) -> str:
    normalized = raw_domain.replace("https://", "").replace("http://", "")
    normalized = normalized.split("/", 1)[0].strip().rstrip("/")
    return normalized


def _parse_positive_int(raw: str | None, default: int, key: str) -> int:
    if raw is None or not str(raw).strip():
        return default
    try:
        value = int(str(raw))
    except ValueError as exc:
        raise ValueError(f"{key} must be a positive integer.") from exc
    if value <= 0:
        raise ValueError(f"{key} must be a positive integer.")
    return value


def parse_cli_args(argv: list[str]) -> dict[str, str]:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--domain", "--storeDomain", "--store-domain", dest="store_domain")
    parser.add_argument(
        "--accessToken",
        "--adminAccessToken",
        "--access-token",
        "--admin-access-token",
        dest="access_token",
    )
    parser.add_argument("--clientId", "--client-id", dest="client_id")
    parser.add_argument("--clientSecret", "--client-secret", dest="client_secret")
    parser.add_argument("--apiVersion", "--api-version", dest="api_version")
    parser.add_argument("--caBundle", "--ca-bundle", dest="ca_bundle")
    parser.add_argument(
        "--oauthRefreshSkewSeconds",
        "--oauth-refresh-skew-seconds",
        dest="oauth_refresh_skew_seconds",
    )
    parser.add_argument(
        "--oauthTokenTtlFallbackSeconds",
        "--oauth-token-ttl-fallback-seconds",
        dest="oauth_token_ttl_fallback_seconds",
    )
    parsed, unknown = parser.parse_known_args(argv)
    if unknown:
        raise ValueError(f"Unknown arguments: {' '.join(unknown)}")

    output: dict[str, str] = {}
    if parsed.store_domain:
        output["SHOPIFY_STORE_DOMAIN"] = parsed.store_domain
    if parsed.access_token:
        output["SHOPIFY_ADMIN_ACCESS_TOKEN"] = parsed.access_token
    if parsed.client_id:
        output["SHOPIFY_CLIENT_ID"] = parsed.client_id
    if parsed.client_secret:
        output["SHOPIFY_CLIENT_SECRET"] = parsed.client_secret
    if parsed.api_version:
        output["SHOPIFY_API_VERSION"] = parsed.api_version
    if parsed.ca_bundle:
        output["SHOPIFY_CA_BUNDLE"] = parsed.ca_bundle
    if parsed.oauth_refresh_skew_seconds:
        output["SHOPIFY_OAUTH_REFRESH_SKEW_SECONDS"] = parsed.oauth_refresh_skew_seconds
    if parsed.oauth_token_ttl_fallback_seconds:
        output["SHOPIFY_OAUTH_TOKEN_TTL_FALLBACK_SECONDS"] = parsed.oauth_token_ttl_fallback_seconds

    return output


def load_config(
    env: Mapping[str, str] | None = None, overrides: Mapping[str, str] | None = None
) -> Config:
    source = dict(env or os.environ)
    if overrides:
        source.update(overrides)

    store_domain = _normalize_store_domain(_require_value(source, "SHOPIFY_STORE_DOMAIN"))
    api_version = source.get("SHOPIFY_API_VERSION", DEFAULT_API_VERSION).strip()

    static_access_token = _optional_value(source, "SHOPIFY_ADMIN_ACCESS_TOKEN")
    client_id = _optional_value(source, "SHOPIFY_CLIENT_ID")
    client_secret = _optional_value(source, "SHOPIFY_CLIENT_SECRET")
    ca_bundle_path = _optional_value(source, "SHOPIFY_CA_BUNDLE") or _optional_value(source, "SSL_CERT_FILE")

    oauth_refresh_skew_seconds = _parse_positive_int(
        source.get("SHOPIFY_OAUTH_REFRESH_SKEW_SECONDS"),
        DEFAULT_OAUTH_REFRESH_SKEW_SECONDS,
        "SHOPIFY_OAUTH_REFRESH_SKEW_SECONDS",
    )
    oauth_token_ttl_fallback_seconds = _parse_positive_int(
        source.get("SHOPIFY_OAUTH_TOKEN_TTL_FALLBACK_SECONDS"),
        DEFAULT_OAUTH_TOKEN_TTL_FALLBACK_SECONDS,
        "SHOPIFY_OAUTH_TOKEN_TTL_FALLBACK_SECONDS",
    )

    if static_access_token:
        auth_mode = "static_token"
    elif client_id or client_secret:
        if not client_id or not client_secret:
            raise ValueError(
                "Both SHOPIFY_CLIENT_ID and SHOPIFY_CLIENT_SECRET are required for client credentials mode."
            )
        auth_mode = "client_credentials"
    else:
        raise ValueError(
            "Missing auth configuration. Set SHOPIFY_ADMIN_ACCESS_TOKEN or SHOPIFY_CLIENT_ID + SHOPIFY_CLIENT_SECRET."
        )

    return Config(
        store_domain=store_domain,
        api_version=api_version,
        auth_mode=auth_mode,
        static_access_token=static_access_token,
        client_id=client_id,
        client_secret=client_secret,
        oauth_refresh_skew_seconds=oauth_refresh_skew_seconds,
        oauth_token_ttl_fallback_seconds=oauth_token_ttl_fallback_seconds,
        ca_bundle_path=ca_bundle_path,
    )

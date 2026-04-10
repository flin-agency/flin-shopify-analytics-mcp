from __future__ import annotations

import time
import unittest
from unittest.mock import patch
from urllib.error import URLError
import ssl

from flin_shopify_analytics_mcp.config import Config
from flin_shopify_analytics_mcp.shopify_client import HttpResponse, ShopifyClient


GRAPHQL_URL = "https://my-shop.myshopify.com/admin/api/2026-04/graphql.json"
TOKEN_URL = "https://my-shop.myshopify.com/admin/oauth/access_token"
DUMMY_QUERY = "query Ping { shop { name } }"


def _config(*, auth_mode: str = "static_token", ca_bundle_path: str | None = None) -> Config:
    return Config(
        store_domain="my-shop.myshopify.com",
        api_version="2026-04",
        auth_mode=auth_mode,
        static_access_token="shpat_static" if auth_mode == "static_token" else None,
        client_id="cid" if auth_mode == "client_credentials" else None,
        client_secret="csecret" if auth_mode == "client_credentials" else None,
        oauth_refresh_skew_seconds=60,
        oauth_token_ttl_fallback_seconds=86399,
        ca_bundle_path=ca_bundle_path,
    )


class ShopifyClientAuthTests(unittest.TestCase):
    def test_static_token_mode_uses_admin_access_token(self) -> None:
        calls: list[tuple[str, dict[str, str], bytes]] = []

        def post_json(url: str, headers: dict[str, str], body: bytes) -> HttpResponse:
            calls.append((url, headers, body))
            return HttpResponse(status=200, payload={"data": {"shop": {"name": "Demo Shop"}}}, status_text="OK")

        client = ShopifyClient(
            _config(),
            post_json=post_json,
        )

        data = client.graphql(DUMMY_QUERY, {})
        self.assertEqual(data["shop"]["name"], "Demo Shop")
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0], GRAPHQL_URL)
        self.assertEqual(calls[0][1]["X-Shopify-Access-Token"], "shpat_static")

    def test_client_credentials_reuses_token_while_valid(self) -> None:
        calls: list[tuple[str, dict[str, str], bytes]] = []

        def post_json(url: str, headers: dict[str, str], body: bytes) -> HttpResponse:
            calls.append((url, headers, body))
            if url == TOKEN_URL:
                return HttpResponse(
                    status=200,
                    payload={"access_token": "dynamic-token-1", "expires_in": 86400},
                    status_text="OK",
                )
            return HttpResponse(status=200, payload={"data": {"shop": {"name": "Demo Shop"}}}, status_text="OK")

        client = ShopifyClient(
            _config(auth_mode="client_credentials"),
            post_json=post_json,
        )

        client.graphql(DUMMY_QUERY, {})
        client.graphql(DUMMY_QUERY, {})
        self.assertEqual(len(calls), 3)
        self.assertEqual(calls[0][0], TOKEN_URL)
        self.assertEqual(calls[1][0], GRAPHQL_URL)
        self.assertEqual(calls[2][0], GRAPHQL_URL)
        self.assertEqual(calls[1][1]["X-Shopify-Access-Token"], "dynamic-token-1")
        self.assertEqual(calls[2][1]["X-Shopify-Access-Token"], "dynamic-token-1")

    def test_client_credentials_refreshes_when_token_near_expiry(self) -> None:
        calls: list[tuple[str, dict[str, str], bytes]] = []
        tokens = [
            {"access_token": "dynamic-token-1", "expires_in": 86400},
            {"access_token": "dynamic-token-2", "expires_in": 86400},
        ]

        def post_json(url: str, headers: dict[str, str], body: bytes) -> HttpResponse:
            calls.append((url, headers, body))
            if url == TOKEN_URL:
                return HttpResponse(status=200, payload=tokens.pop(0), status_text="OK")
            return HttpResponse(status=200, payload={"data": {"shop": {"name": "Demo Shop"}}}, status_text="OK")

        client = ShopifyClient(
            _config(auth_mode="client_credentials"),
            post_json=post_json,
        )

        client.graphql(DUMMY_QUERY, {})
        client.cached_token_expires_at = time.time() + 0.5
        client.graphql(DUMMY_QUERY, {})

        self.assertEqual(len(calls), 4)
        self.assertEqual(calls[0][0], TOKEN_URL)
        self.assertEqual(calls[1][0], GRAPHQL_URL)
        self.assertEqual(calls[2][0], TOKEN_URL)
        self.assertEqual(calls[3][0], GRAPHQL_URL)
        self.assertEqual(calls[1][1]["X-Shopify-Access-Token"], "dynamic-token-1")
        self.assertEqual(calls[3][1]["X-Shopify-Access-Token"], "dynamic-token-2")

    def test_default_client_uses_certifi_ca_bundle(self) -> None:
        captured: dict[str, object] = {}

        class _Response:
            status = 200
            reason = "OK"

            def read(self) -> bytes:
                return b'{"data":{"shop":{"name":"Demo Shop"}}}'

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        def fake_create_default_context(*, cafile=None):
            captured["cafile"] = cafile
            return "ssl-context"

        def fake_urlopen(request, timeout=30, context=None):
            captured["context"] = context
            return _Response()

        with (
            patch("flin_shopify_analytics_mcp.shopify_client.certifi.where", return_value="/tmp/certifi.pem"),
            patch(
                "flin_shopify_analytics_mcp.shopify_client.ssl.create_default_context",
                side_effect=fake_create_default_context,
            ),
            patch("flin_shopify_analytics_mcp.shopify_client.urlopen", side_effect=fake_urlopen),
        ):
            client = ShopifyClient(_config())
            data = client.graphql(DUMMY_QUERY, {})

        self.assertEqual(data["shop"]["name"], "Demo Shop")
        self.assertEqual(captured["cafile"], "/tmp/certifi.pem")
        self.assertEqual(captured["context"], "ssl-context")

    def test_ssl_verification_error_has_actionable_message(self) -> None:
        ssl_error = ssl.SSLCertVerificationError("CERTIFICATE_VERIFY_FAILED")
        with (
            patch("flin_shopify_analytics_mcp.shopify_client.certifi.where", return_value="/tmp/certifi.pem"),
            patch("flin_shopify_analytics_mcp.shopify_client.ssl.create_default_context", return_value="ssl-context"),
            patch("flin_shopify_analytics_mcp.shopify_client.urlopen", side_effect=URLError(ssl_error)),
        ):
            client = ShopifyClient(_config(ca_bundle_path="/tmp/custom-ca.pem"))
            with self.assertRaises(RuntimeError) as ctx:
                client.graphql(DUMMY_QUERY, {})

        message = str(ctx.exception)
        self.assertIn("SSL certificate verification failed", message)
        self.assertIn("SHOPIFY_CA_BUNDLE", message)


if __name__ == "__main__":
    unittest.main()

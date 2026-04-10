from __future__ import annotations

import time
import unittest

from flin_shopify_analytics_mcp.config import Config
from flin_shopify_analytics_mcp.shopify_client import HttpResponse, ShopifyClient


GRAPHQL_URL = "https://my-shop.myshopify.com/admin/api/2025-01/graphql.json"
TOKEN_URL = "https://my-shop.myshopify.com/admin/oauth/access_token"
DUMMY_QUERY = "query Ping { shop { name } }"


class ShopifyClientAuthTests(unittest.TestCase):
    def test_static_token_mode_uses_admin_access_token(self) -> None:
        calls: list[tuple[str, dict[str, str], bytes]] = []

        def post_json(url: str, headers: dict[str, str], body: bytes) -> HttpResponse:
            calls.append((url, headers, body))
            return HttpResponse(status=200, payload={"data": {"shop": {"name": "Demo Shop"}}}, status_text="OK")

        client = ShopifyClient(
            Config(
                store_domain="my-shop.myshopify.com",
                api_version="2025-01",
                auth_mode="static_token",
                static_access_token="shpat_static",
                client_id=None,
                client_secret=None,
                oauth_refresh_skew_seconds=60,
                oauth_token_ttl_fallback_seconds=86399,
            ),
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
            Config(
                store_domain="my-shop.myshopify.com",
                api_version="2025-01",
                auth_mode="client_credentials",
                static_access_token=None,
                client_id="cid",
                client_secret="csecret",
                oauth_refresh_skew_seconds=60,
                oauth_token_ttl_fallback_seconds=86399,
            ),
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
            Config(
                store_domain="my-shop.myshopify.com",
                api_version="2025-01",
                auth_mode="client_credentials",
                static_access_token=None,
                client_id="cid",
                client_secret="csecret",
                oauth_refresh_skew_seconds=60,
                oauth_token_ttl_fallback_seconds=86399,
            ),
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


if __name__ == "__main__":
    unittest.main()

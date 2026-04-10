from __future__ import annotations

import unittest

from flin_shopify_analytics_mcp.config import load_config, parse_cli_args


class ConfigTests(unittest.TestCase):
    def test_load_config_raises_when_required_env_missing(self) -> None:
        with self.assertRaisesRegex(ValueError, "SHOPIFY_STORE_DOMAIN"):
            load_config({})

    def test_load_config_raises_when_auth_missing(self) -> None:
        with self.assertRaisesRegex(ValueError, "SHOPIFY_ADMIN_ACCESS_TOKEN"):
            load_config({"SHOPIFY_STORE_DOMAIN": "my-shop.myshopify.com"})

    def test_load_config_static_token_mode(self) -> None:
        config = load_config(
            {
                "SHOPIFY_STORE_DOMAIN": "https://my-shop.myshopify.com/",
                "SHOPIFY_ADMIN_ACCESS_TOKEN": "secret-token",
            }
        )
        self.assertEqual(config.store_domain, "my-shop.myshopify.com")
        self.assertEqual(config.auth_mode, "static_token")
        self.assertEqual(config.static_access_token, "secret-token")
        self.assertIsNone(config.client_id)
        self.assertIsNone(config.client_secret)
        self.assertEqual(config.api_version, "2026-04")
        self.assertEqual(config.oauth_refresh_skew_seconds, 60)
        self.assertEqual(config.oauth_token_ttl_fallback_seconds, 86399)

    def test_load_config_client_credentials_mode(self) -> None:
        config = load_config(
            {
                "SHOPIFY_STORE_DOMAIN": "my-shop.myshopify.com",
                "SHOPIFY_CLIENT_ID": "cid",
                "SHOPIFY_CLIENT_SECRET": "csecret",
                "SHOPIFY_OAUTH_REFRESH_SKEW_SECONDS": "120",
                "SHOPIFY_OAUTH_TOKEN_TTL_FALLBACK_SECONDS": "7200",
            }
        )
        self.assertEqual(config.auth_mode, "client_credentials")
        self.assertEqual(config.client_id, "cid")
        self.assertEqual(config.client_secret, "csecret")
        self.assertEqual(config.oauth_refresh_skew_seconds, 120)
        self.assertEqual(config.oauth_token_ttl_fallback_seconds, 7200)

    def test_parse_cli_args_maps_flags(self) -> None:
        parsed = parse_cli_args(
            [
                "--domain",
                "my-shop.myshopify.com",
                "--clientId",
                "id-1",
                "--clientSecret",
                "sec-1",
                "--apiVersion",
                "2026-01",
            ]
        )
        self.assertEqual(
            parsed,
            {
                "SHOPIFY_STORE_DOMAIN": "my-shop.myshopify.com",
                "SHOPIFY_CLIENT_ID": "id-1",
                "SHOPIFY_CLIENT_SECRET": "sec-1",
                "SHOPIFY_API_VERSION": "2026-01",
            },
        )


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import unittest

from flin_shopify_analytics_mcp.config import Config
from flin_shopify_analytics_mcp.shopify_client import HttpResponse, ShopifyClient


class ShopifyClientOrderMappingTests(unittest.TestCase):
    def test_list_orders_maps_reporting_fields(self) -> None:
        def post_json(_url: str, _headers: dict[str, str], _body: bytes) -> HttpResponse:
            return HttpResponse(
                status=200,
                payload={
                    "data": {
                        "orders": {
                            "edges": [
                                {
                                    "node": {
                                        "id": "gid://shopify/Order/1",
                                        "name": "#1001",
                                        "createdAt": "2026-04-10T10:00:00Z",
                                        "totalPriceSet": {"shopMoney": {"amount": "100.00", "currencyCode": "USD"}},
                                        "subtotalPriceSet": {"shopMoney": {"amount": "90.00", "currencyCode": "USD"}},
                                        "totalDiscountsSet": {"shopMoney": {"amount": "10.00", "currencyCode": "USD"}},
                                        "totalRefundedSet": {"shopMoney": {"amount": "20.00", "currencyCode": "USD"}},
                                        "currentSubtotalLineItemsQuantity": 2,
                                        "discountCodes": ["SPRING10"],
                                        "sourceName": "web",
                                        "customerJourneySummary": {
                                            "ready": True,
                                            "lastVisit": {
                                                "landingPage": "https://shop.example.com/products/shirt?utm_source=instagram&utm_medium=paid-social&utm_campaign=spring",
                                                "referrerUrl": "https://instagram.com/story/123",
                                                "source": "instagram",
                                                "utmParameters": {
                                                    "source": "instagram",
                                                    "medium": "paid-social",
                                                    "campaign": "spring",
                                                    "term": None,
                                                    "content": None,
                                                },
                                            },
                                        },
                                        "customer": {
                                            "id": "gid://shopify/Customer/42",
                                            "displayName": "Alice",
                                            "email": "alice@example.com",
                                            "numberOfOrders": 3,
                                        },
                                        "lineItems": {
                                            "edges": [
                                                {
                                                    "node": {
                                                        "title": "Shirt",
                                                        "sku": "SHIRT-1",
                                                        "quantity": 2,
                                                        "currentQuantity": 1,
                                                        "variantTitle": "Blue / M",
                                                        "originalUnitPriceSet": {
                                                            "shopMoney": {"amount": "50.00", "currencyCode": "USD"}
                                                        },
                                                        "discountedUnitPriceAfterAllDiscountsSet": {
                                                            "shopMoney": {"amount": "45.00", "currencyCode": "USD"}
                                                        },
                                                        "originalTotalSet": {
                                                            "shopMoney": {"amount": "100.00", "currencyCode": "USD"}
                                                        },
                                                        "totalDiscountSet": {
                                                            "shopMoney": {"amount": "10.00", "currencyCode": "USD"}
                                                        },
                                                        "variant": {
                                                            "id": "gid://shopify/ProductVariant/5",
                                                            "title": "Blue / M",
                                                            "sku": "SHIRT-1",
                                                        },
                                                        "product": {
                                                            "id": "gid://shopify/Product/5",
                                                            "title": "Shirt",
                                                        },
                                                    }
                                                }
                                            ]
                                        },
                                    }
                                }
                            ],
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                        }
                    }
                },
                status_text="OK",
            )

        client = ShopifyClient(
            Config(
                store_domain="my-shop.myshopify.com",
                api_version="2026-04",
                auth_mode="static_token",
                static_access_token="shpat_static",
                client_id=None,
                client_secret=None,
                oauth_refresh_skew_seconds=60,
                oauth_token_ttl_fallback_seconds=86399,
                ca_bundle_path=None,
            ),
            post_json=post_json,
        )

        orders = client.list_orders(limit=10)
        self.assertEqual(len(orders), 1)
        order = orders[0]
        self.assertEqual(order["subtotalAmount"], 90.0)
        self.assertEqual(order["discountAmount"], 10.0)
        self.assertEqual(order["refundedAmount"], 20.0)
        self.assertEqual(order["grossSales"], 100.0)
        self.assertEqual(order["netSales"], 70.0)
        self.assertEqual(order["unitsSold"], 2)
        self.assertEqual(order["discountCodes"], ["SPRING10"])
        self.assertEqual(order["sourceName"], "instagram")
        self.assertTrue(order["attributionReady"])
        self.assertEqual(
            order["landingPage"],
            "https://shop.example.com/products/shirt?utm_source=instagram&utm_medium=paid-social&utm_campaign=spring",
        )
        self.assertEqual(order["referringSite"], "https://instagram.com/story/123")
        self.assertEqual(order["utm"]["campaign"], "spring")
        self.assertEqual(order["customer"]["numberOfOrders"], 3)
        self.assertEqual(order["items"][0]["variantId"], "gid://shopify/ProductVariant/5")
        self.assertEqual(order["items"][0]["unitPrice"], 50.0)
        self.assertEqual(order["items"][0]["discountedUnitPrice"], 45.0)
        self.assertEqual(order["items"][0]["grossSales"], 100.0)
        self.assertEqual(order["items"][0]["netSales"], 45.0)
        self.assertEqual(order["items"][0]["discountAmount"], 10.0)


if __name__ == "__main__":
    unittest.main()

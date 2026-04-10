from __future__ import annotations

import unittest

from flin_shopify_analytics_mcp.analytics import aggregate_by_customer_product


class AnalyticsTests(unittest.TestCase):
    def test_aggregate_groups_quantities_and_spend(self) -> None:
        orders = [
            {
                "id": "gid://shopify/Order/1",
                "totalAmount": 100,
                "currencyCode": "USD",
                "customer": {
                    "id": "gid://shopify/Customer/10",
                    "name": "Alice",
                    "email": "alice@example.com",
                },
                "items": [
                    {
                        "productId": "gid://shopify/Product/500",
                        "title": "T-Shirt",
                        "sku": "TS-1",
                        "quantity": 2,
                    },
                    {
                        "productId": "gid://shopify/Product/600",
                        "title": "Cap",
                        "sku": "CAP-1",
                        "quantity": 1,
                    },
                ],
            },
            {
                "id": "gid://shopify/Order/2",
                "totalAmount": 50,
                "currencyCode": "USD",
                "customer": {
                    "id": "gid://shopify/Customer/10",
                    "name": "Alice",
                    "email": "alice@example.com",
                },
                "items": [
                    {
                        "productId": "gid://shopify/Product/500",
                        "title": "T-Shirt",
                        "sku": "TS-1",
                        "quantity": 1,
                    }
                ],
            },
        ]
        result = aggregate_by_customer_product(orders)
        self.assertEqual(result["orderCount"], 2)
        self.assertEqual(result["customerCount"], 1)
        customer = result["customers"][0]
        self.assertEqual(customer["totalOrders"], 2)
        self.assertEqual(customer["totalSpent"], 150)
        self.assertEqual(
            customer["products"],
            [
                {
                    "productId": "gid://shopify/Product/500",
                    "title": "T-Shirt",
                    "sku": "TS-1",
                    "quantity": 3,
                },
                {
                    "productId": "gid://shopify/Product/600",
                    "title": "Cap",
                    "sku": "CAP-1",
                    "quantity": 1,
                },
            ],
        )


if __name__ == "__main__":
    unittest.main()

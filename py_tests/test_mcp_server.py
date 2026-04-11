from __future__ import annotations

import unittest

from flin_shopify_analytics_mcp.mcp_server import ShopifyAnalyticsMcpServer


class FakeShopifyClient:
    def list_orders(self, **_kwargs):
        created_after = _kwargs.get("createdAfter")
        created_before = _kwargs.get("createdBefore")
        if created_after is None and created_before is not None:
            return [
                {
                    "id": "gid://shopify/Order/101",
                    "name": "#1101",
                    "createdAt": "2026-01-10T10:00:00Z",
                    "totalAmount": 100,
                    "subtotalAmount": 100,
                    "discountAmount": 0,
                    "refundedAmount": 0,
                    "grossSales": 100,
                    "netSales": 100,
                    "unitsSold": 1,
                    "currencyCode": "USD",
                    "discountCodes": [],
                    "customer": {
                        "id": "gid://shopify/Customer/101",
                        "name": "Alice",
                        "email": "alice@example.com",
                        "numberOfOrders": 2,
                    },
                    "items": [],
                },
                {
                    "id": "gid://shopify/Order/102",
                    "name": "#1102",
                    "createdAt": "2026-01-25T10:00:00Z",
                    "totalAmount": 90,
                    "subtotalAmount": 90,
                    "discountAmount": 0,
                    "refundedAmount": 0,
                    "grossSales": 90,
                    "netSales": 90,
                    "unitsSold": 1,
                    "currencyCode": "USD",
                    "discountCodes": [],
                    "customer": {
                        "id": "gid://shopify/Customer/101",
                        "name": "Alice",
                        "email": "alice@example.com",
                        "numberOfOrders": 2,
                    },
                    "items": [],
                },
                {
                    "id": "gid://shopify/Order/201",
                    "name": "#1201",
                    "createdAt": "2026-01-20T10:00:00Z",
                    "totalAmount": 120,
                    "subtotalAmount": 120,
                    "discountAmount": 0,
                    "refundedAmount": 0,
                    "grossSales": 120,
                    "netSales": 120,
                    "unitsSold": 1,
                    "currencyCode": "USD",
                    "discountCodes": [],
                    "customer": {
                        "id": "gid://shopify/Customer/202",
                        "name": "Bob",
                        "email": "bob@example.com",
                        "numberOfOrders": 1,
                    },
                    "items": [],
                },
            ]
        return [
            {
                "id": "gid://shopify/Order/1",
                "name": "#1001",
                "createdAt": "2026-04-10T10:00:00Z",
                "totalAmount": 100,
                "subtotalAmount": 90,
                "discountAmount": 10,
                "refundedAmount": 0,
                "grossSales": 100,
                "netSales": 90,
                "unitsSold": 2,
                "currencyCode": "USD",
                "discountCodes": ["SPRING10"],
                "customer": {
                    "id": "gid://shopify/Customer/42",
                    "name": "Alice",
                    "email": "alice@example.com",
                    "numberOfOrders": 1,
                },
                "items": [
                    {
                        "productId": "gid://shopify/Product/5",
                        "variantId": "gid://shopify/ProductVariant/50",
                        "title": "Shirt",
                        "variantTitle": "Blue / M",
                        "sku": "SHIRT-1",
                        "quantity": 2,
                        "currentQuantity": 2,
                        "grossSales": 100,
                        "netSales": 90,
                        "discountAmount": 10,
                    }
                ],
            }
        ]

    def list_customers(self, **_kwargs):
        return [{"id": "gid://shopify/Customer/42", "displayName": "Alice", "email": "alice@example.com"}]

    def list_products(self, **_kwargs):
        return [{"id": "gid://shopify/Product/5", "title": "Shirt", "handle": "shirt"}]

    def customer_purchase_summary(self, **_kwargs):
        return {
            "customer": {"id": "gid://shopify/Customer/42", "name": "Alice", "email": "alice@example.com"},
            "totalOrders": 1,
            "totalSpent": 100,
            "currencyCode": "USD",
            "products": [
                {
                    "productId": "gid://shopify/Product/5",
                    "title": "Shirt",
                    "sku": "SHIRT-1",
                    "quantity": 2,
                }
            ],
        }


class McpServerTests(unittest.TestCase):
    def test_initialize_returns_capabilities(self) -> None:
        server = ShopifyAnalyticsMcpServer(client=FakeShopifyClient())
        response = server.handle_message(
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-03-26"}}
        )
        assert response is not None
        self.assertEqual(response["result"]["protocolVersion"], "2025-03-26")
        self.assertIn("tools", response["result"]["capabilities"])
        self.assertIn("resources", response["result"]["capabilities"])
        self.assertIn("instructions", response["result"])

    def test_tools_list_returns_read_only_tools(self) -> None:
        server = ShopifyAnalyticsMcpServer(client=FakeShopifyClient())
        server.handle_message(
            {"jsonrpc": "2.0", "id": 99, "method": "initialize", "params": {"protocolVersion": "2025-03-26"}}
        )
        response = server.handle_message({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}})
        assert response is not None
        names = [tool["name"] for tool in response["result"]["tools"]]
        self.assertEqual(
            names,
            [
                "shopify_list_orders",
                "shopify_list_customers",
                "shopify_list_products",
                "shopify_customer_purchase_summary",
                "shopify_sales_by_customer_product",
                "shopify_sales_overview",
                "shopify_sales_timeseries",
                "shopify_top_products",
                "shopify_top_customers",
                "shopify_discount_analysis",
                "shopify_retention_overview",
                "shopify_repeat_purchase_windows",
                "shopify_time_to_second_order",
                "shopify_inactive_customer_summary",
            ],
        )

    def test_tools_call_returns_structured_output(self) -> None:
        server = ShopifyAnalyticsMcpServer(client=FakeShopifyClient())
        server.handle_message(
            {"jsonrpc": "2.0", "id": 99, "method": "initialize", "params": {"protocolVersion": "2025-03-26"}}
        )
        response = server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": "shopify_sales_by_customer_product", "arguments": {"limit": 10}},
            }
        )
        assert response is not None
        summary = response["result"]["structuredContent"]
        self.assertEqual(summary["orderCount"], 1)
        self.assertEqual(summary["customers"][0]["products"][0]["quantity"], 2)

    def test_reporting_tool_returns_structured_output(self) -> None:
        server = ShopifyAnalyticsMcpServer(client=FakeShopifyClient())
        server.handle_message(
            {"jsonrpc": "2.0", "id": 99, "method": "initialize", "params": {"protocolVersion": "2025-03-26"}}
        )
        response = server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "shopify_sales_overview",
                    "arguments": {
                        "dateFrom": "2026-04-01T00:00:00Z",
                        "dateTo": "2026-04-30T23:59:59Z",
                    },
                },
            }
        )
        assert response is not None
        summary = response["result"]["structuredContent"]
        self.assertEqual(summary["currentPeriod"]["orders"], 1)
        self.assertEqual(summary["currentPeriod"]["netSales"], 90)

    def test_retention_tool_returns_structured_output(self) -> None:
        server = ShopifyAnalyticsMcpServer(client=FakeShopifyClient())
        server.handle_message(
            {"jsonrpc": "2.0", "id": 99, "method": "initialize", "params": {"protocolVersion": "2025-03-26"}}
        )
        response = server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "shopify_repeat_purchase_windows",
                    "arguments": {
                        "dateFrom": "2026-01-01T00:00:00Z",
                        "dateTo": "2026-01-31T23:59:59Z",
                        "asOfDate": "2026-04-30T23:59:59Z",
                    },
                },
            }
        )
        assert response is not None
        summary = response["result"]["structuredContent"]
        self.assertEqual(summary["cohortCustomers"], 2)
        self.assertEqual(summary["windows"][0]["windowDays"], 30)


if __name__ == "__main__":
    unittest.main()

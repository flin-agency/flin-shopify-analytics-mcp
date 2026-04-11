from __future__ import annotations

import unittest

from flin_shopify_analytics_mcp.analytics import (
    aggregate_by_customer_product,
    discount_analysis,
    inactive_customer_summary,
    repeat_purchase_windows,
    retention_overview,
    sales_overview,
    sales_timeseries,
    time_to_second_order,
    top_customers,
    top_products,
)


ORDERS = [
    {
        "id": "gid://shopify/Order/1",
        "name": "#1001",
        "createdAt": "2026-04-01T10:00:00Z",
        "totalAmount": 100.0,
        "subtotalAmount": 90.0,
        "discountAmount": 10.0,
        "refundedAmount": 0.0,
        "grossSales": 100.0,
        "netSales": 90.0,
        "unitsSold": 3,
        "currencyCode": "USD",
        "discountCodes": ["SPRING10"],
        "customer": {
            "id": "gid://shopify/Customer/10",
            "name": "Alice",
            "email": "alice@example.com",
            "numberOfOrders": 1,
        },
        "items": [
            {
                "productId": "gid://shopify/Product/500",
                "variantId": "gid://shopify/ProductVariant/501",
                "title": "T-Shirt",
                "variantTitle": "Blue / M",
                "sku": "TS-1",
                "quantity": 2,
                "currentQuantity": 2,
                "grossSales": 60.0,
                "netSales": 54.0,
                "discountAmount": 6.0,
            },
            {
                "productId": "gid://shopify/Product/600",
                "variantId": "gid://shopify/ProductVariant/601",
                "title": "Cap",
                "variantTitle": "Black",
                "sku": "CAP-1",
                "quantity": 1,
                "currentQuantity": 1,
                "grossSales": 40.0,
                "netSales": 36.0,
                "discountAmount": 4.0,
            },
        ],
    },
    {
        "id": "gid://shopify/Order/2",
        "name": "#1002",
        "createdAt": "2026-04-02T12:00:00Z",
        "totalAmount": 120.0,
        "subtotalAmount": 120.0,
        "discountAmount": 0.0,
        "refundedAmount": 20.0,
        "grossSales": 120.0,
        "netSales": 100.0,
        "unitsSold": 3,
        "currencyCode": "USD",
        "discountCodes": [],
        "customer": {
            "id": "gid://shopify/Customer/20",
            "name": "Bob",
            "email": "bob@example.com",
            "numberOfOrders": 3,
        },
        "items": [
            {
                "productId": "gid://shopify/Product/500",
                "variantId": "gid://shopify/ProductVariant/502",
                "title": "T-Shirt",
                "variantTitle": "Red / L",
                "sku": "TS-2",
                "quantity": 3,
                "currentQuantity": 3,
                "grossSales": 120.0,
                "netSales": 100.0,
                "discountAmount": 0.0,
            }
        ],
    },
    {
        "id": "gid://shopify/Order/3",
        "name": "#1003",
        "createdAt": "2026-04-08T08:00:00Z",
        "totalAmount": 80.0,
        "subtotalAmount": 75.0,
        "discountAmount": 5.0,
        "refundedAmount": 0.0,
        "grossSales": 80.0,
        "netSales": 75.0,
        "unitsSold": 2,
        "currencyCode": "USD",
        "discountCodes": ["VIP5"],
        "customer": {
            "id": "gid://shopify/Customer/20",
            "name": "Bob",
            "email": "bob@example.com",
            "numberOfOrders": 3,
        },
        "items": [
            {
                "productId": "gid://shopify/Product/700",
                "variantId": "gid://shopify/ProductVariant/701",
                "title": "Mug",
                "variantTitle": "Default",
                "sku": "MUG-1",
                "quantity": 2,
                "currentQuantity": 2,
                "grossSales": 80.0,
                "netSales": 75.0,
                "discountAmount": 5.0,
            }
        ],
    },
]

RETENTION_ORDERS = [
    {
        "id": "gid://shopify/Order/101",
        "createdAt": "2026-01-10T10:00:00Z",
        "netSales": 100.0,
        "grossSales": 110.0,
        "discountAmount": 10.0,
        "refundedAmount": 0.0,
        "unitsSold": 2,
        "currencyCode": "USD",
        "customer": {"id": "gid://shopify/Customer/1", "name": "Alice", "email": "alice@example.com"},
        "items": [],
    },
    {
        "id": "gid://shopify/Order/102",
        "createdAt": "2026-01-25T10:00:00Z",
        "netSales": 90.0,
        "grossSales": 90.0,
        "discountAmount": 0.0,
        "refundedAmount": 0.0,
        "unitsSold": 1,
        "currencyCode": "USD",
        "customer": {"id": "gid://shopify/Customer/1", "name": "Alice", "email": "alice@example.com"},
        "items": [],
    },
    {
        "id": "gid://shopify/Order/103",
        "createdAt": "2026-03-01T10:00:00Z",
        "netSales": 70.0,
        "grossSales": 70.0,
        "discountAmount": 0.0,
        "refundedAmount": 0.0,
        "unitsSold": 1,
        "currencyCode": "USD",
        "customer": {"id": "gid://shopify/Customer/1", "name": "Alice", "email": "alice@example.com"},
        "items": [],
    },
    {
        "id": "gid://shopify/Order/201",
        "createdAt": "2026-01-20T10:00:00Z",
        "netSales": 120.0,
        "grossSales": 120.0,
        "discountAmount": 0.0,
        "refundedAmount": 0.0,
        "unitsSold": 2,
        "currencyCode": "USD",
        "customer": {"id": "gid://shopify/Customer/2", "name": "Bob", "email": "bob@example.com"},
        "items": [],
    },
    {
        "id": "gid://shopify/Order/202",
        "createdAt": "2026-03-10T10:00:00Z",
        "netSales": 110.0,
        "grossSales": 110.0,
        "discountAmount": 0.0,
        "refundedAmount": 0.0,
        "unitsSold": 2,
        "currencyCode": "USD",
        "customer": {"id": "gid://shopify/Customer/2", "name": "Bob", "email": "bob@example.com"},
        "items": [],
    },
    {
        "id": "gid://shopify/Order/301",
        "createdAt": "2026-01-28T10:00:00Z",
        "netSales": 80.0,
        "grossSales": 80.0,
        "discountAmount": 0.0,
        "refundedAmount": 0.0,
        "unitsSold": 1,
        "currencyCode": "USD",
        "customer": {"id": "gid://shopify/Customer/3", "name": "Carol", "email": "carol@example.com"},
        "items": [],
    },
    {
        "id": "gid://shopify/Order/401",
        "createdAt": "2025-09-01T10:00:00Z",
        "netSales": 95.0,
        "grossSales": 95.0,
        "discountAmount": 0.0,
        "refundedAmount": 0.0,
        "unitsSold": 1,
        "currencyCode": "USD",
        "customer": {"id": "gid://shopify/Customer/4", "name": "Dana", "email": "dana@example.com"},
        "items": [],
    },
    {
        "id": "gid://shopify/Order/402",
        "createdAt": "2025-10-01T10:00:00Z",
        "netSales": 105.0,
        "grossSales": 105.0,
        "discountAmount": 0.0,
        "refundedAmount": 0.0,
        "unitsSold": 1,
        "currencyCode": "USD",
        "customer": {"id": "gid://shopify/Customer/4", "name": "Dana", "email": "dana@example.com"},
        "items": [],
    },
    {
        "id": "gid://shopify/Order/501",
        "createdAt": "2026-03-01T10:00:00Z",
        "netSales": 75.0,
        "grossSales": 75.0,
        "discountAmount": 0.0,
        "refundedAmount": 0.0,
        "unitsSold": 1,
        "currencyCode": "USD",
        "customer": {"id": "gid://shopify/Customer/5", "name": "Eve", "email": "eve@example.com"},
        "items": [],
    },
    {
        "id": "gid://shopify/Order/502",
        "createdAt": "2026-04-20T10:00:00Z",
        "netSales": 85.0,
        "grossSales": 85.0,
        "discountAmount": 0.0,
        "refundedAmount": 0.0,
        "unitsSold": 1,
        "currencyCode": "USD",
        "customer": {"id": "gid://shopify/Customer/5", "name": "Eve", "email": "eve@example.com"},
        "items": [],
    },
]


class AnalyticsTests(unittest.TestCase):
    def test_aggregate_groups_quantities_and_spend(self) -> None:
        result = aggregate_by_customer_product(ORDERS[:2])
        self.assertEqual(result["orderCount"], 2)
        self.assertEqual(result["customerCount"], 2)
        customer = result["customers"][0]
        self.assertEqual(customer["customerName"], "Bob")
        self.assertEqual(customer["totalOrders"], 1)
        self.assertEqual(customer["totalSpent"], 120)

    def test_sales_overview_calculates_period_metrics_and_previous_period(self) -> None:
        result = sales_overview(
            ORDERS,
            date_from="2026-04-01T00:00:00Z",
            date_to="2026-04-07T23:59:59Z",
            compare_previous_period=True,
        )
        current = result["currentPeriod"]
        self.assertEqual(current["orders"], 2)
        self.assertEqual(current["unitsSold"], 6)
        self.assertEqual(current["grossSales"], 220.0)
        self.assertEqual(current["discountAmount"], 10.0)
        self.assertEqual(current["refundedAmount"], 20.0)
        self.assertEqual(current["netSales"], 190.0)
        self.assertEqual(current["averageOrderValue"], 95.0)
        self.assertEqual(current["newCustomerOrders"], 1)
        self.assertEqual(current["returningCustomerOrders"], 1)
        self.assertEqual(result["previousPeriod"]["orders"], 0)
        self.assertEqual(result["delta"]["netSales"], 190.0)

    def test_sales_timeseries_groups_by_day(self) -> None:
        result = sales_timeseries(
            ORDERS,
            date_from="2026-04-01T00:00:00Z",
            date_to="2026-04-08T23:59:59Z",
            interval="day",
        )
        self.assertEqual(len(result["buckets"]), 3)
        self.assertEqual(result["buckets"][0]["label"], "2026-04-01")
        self.assertEqual(result["buckets"][0]["netSales"], 90.0)
        self.assertEqual(result["buckets"][1]["orders"], 1)
        self.assertEqual(result["buckets"][1]["refundedAmount"], 20.0)
        self.assertEqual(result["buckets"][2]["label"], "2026-04-08")

    def test_top_products_ranks_by_net_sales(self) -> None:
        result = top_products(
            ORDERS,
            date_from="2026-04-01T00:00:00Z",
            date_to="2026-04-30T23:59:59Z",
            sort_by="netSales",
            group_by="product",
            limit=3,
        )
        self.assertEqual(result["rows"][0]["productId"], "gid://shopify/Product/500")
        self.assertEqual(result["rows"][0]["netSales"], 154.0)
        self.assertEqual(result["rows"][0]["unitsSold"], 5)

    def test_top_customers_filters_returning(self) -> None:
        result = top_customers(
            ORDERS,
            date_from="2026-04-01T00:00:00Z",
            date_to="2026-04-30T23:59:59Z",
            sort_by="netSales",
            customer_type="returning",
            limit=10,
        )
        self.assertEqual(len(result["rows"]), 1)
        self.assertEqual(result["rows"][0]["customerId"], "gid://shopify/Customer/20")
        self.assertEqual(result["rows"][0]["netSales"], 175.0)
        self.assertEqual(result["rows"][0]["orders"], 2)

    def test_discount_analysis_summarizes_codes(self) -> None:
        result = discount_analysis(
            ORDERS,
            date_from="2026-04-01T00:00:00Z",
            date_to="2026-04-30T23:59:59Z",
            limit=10,
        )
        self.assertEqual(result["discountAmountTotal"], 15.0)
        self.assertEqual(result["discountedOrders"], 2)
        self.assertAlmostEqual(result["discountedOrderRate"], 2 / 3, places=4)
        self.assertEqual(result["averageDiscountPerDiscountedOrder"], 7.5)
        self.assertEqual(result["topDiscountCodes"][0]["code"], "SPRING10")
        self.assertEqual(result["topDiscountCodes"][0]["orders"], 1)

    def test_retention_overview_summarizes_cohort_repeat_behavior(self) -> None:
        result = retention_overview(
            RETENTION_ORDERS,
            date_from="2026-01-01T00:00:00Z",
            date_to="2026-01-31T23:59:59Z",
            as_of_date="2026-04-30T23:59:59Z",
        )
        self.assertEqual(result["cohortCustomers"], 3)
        self.assertEqual(result["repeatCustomers"], 2)
        self.assertAlmostEqual(result["repeatCustomerRate"], 2 / 3, places=4)
        self.assertEqual(result["firstOrderNetSales"], 300.0)
        self.assertEqual(result["repeatOrderNetSales"], 270.0)
        self.assertEqual(result["repeatOrders"], 3)
        self.assertEqual(result["averageDaysToSecondOrder"], 32.0)
        self.assertEqual(result["medianDaysToSecondOrder"], 32.0)

    def test_repeat_purchase_windows_returns_eligible_and_repeat_rates(self) -> None:
        result = repeat_purchase_windows(
            RETENTION_ORDERS,
            date_from="2026-01-01T00:00:00Z",
            date_to="2026-01-31T23:59:59Z",
            as_of_date="2026-04-30T23:59:59Z",
        )
        rows = {row["windowDays"]: row for row in result["windows"]}
        self.assertEqual(rows[30]["eligibleCustomers"], 3)
        self.assertEqual(rows[30]["repeatedCustomers"], 1)
        self.assertAlmostEqual(rows[30]["repeatRate"], 1 / 3, places=4)
        self.assertEqual(rows[60]["repeatedCustomers"], 2)
        self.assertAlmostEqual(rows[60]["repeatRate"], 2 / 3, places=4)
        self.assertEqual(rows[180]["eligibleCustomers"], 0)

    def test_time_to_second_order_returns_distribution(self) -> None:
        result = time_to_second_order(
            RETENTION_ORDERS,
            date_from="2026-01-01T00:00:00Z",
            date_to="2026-01-31T23:59:59Z",
            as_of_date="2026-04-30T23:59:59Z",
        )
        self.assertEqual(result["cohortCustomers"], 3)
        self.assertEqual(result["customersWithSecondOrder"], 2)
        self.assertEqual(result["averageDays"], 32.0)
        self.assertEqual(result["medianDays"], 32.0)
        self.assertEqual(result["p75Days"], 49.0)
        self.assertEqual(result["distribution"]["0-30"], 1)
        self.assertEqual(result["distribution"]["31-60"], 1)

    def test_inactive_customer_summary_buckets_customers_by_days_since_last_order(self) -> None:
        result = inactive_customer_summary(RETENTION_ORDERS, as_of_date="2026-04-30T23:59:59Z")
        windows = {row["windowDays"]: row for row in result["windows"]}
        self.assertEqual(result["trackedCustomers"], 5)
        self.assertEqual(windows[30]["inactiveCustomers"], 4)
        self.assertEqual(windows[90]["inactiveCustomers"], 2)
        self.assertAlmostEqual(windows[90]["inactiveRate"], 0.4, places=4)
        self.assertEqual(windows[90]["historicalNetSales"], 280.0)


if __name__ == "__main__":
    unittest.main()

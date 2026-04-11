"""MCP tool declarations and dispatch."""

from __future__ import annotations

import json
from typing import Any

from .analytics import (
    aggregate_by_customer_product,
    discount_analysis,
    inactive_customer_summary,
    previous_period_window,
    repeat_purchase_windows,
    retention_overview,
    sales_overview,
    sales_timeseries,
    time_to_second_order,
    top_customers,
    top_products,
)


TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "shopify_list_orders",
        "description": "List read-only Shopify orders with customer, amount and line items.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "minimum": 1, "maximum": 1000, "default": 50},
                "query": {"type": "string", "description": "Shopify order search query."},
                "createdAfter": {"type": "string", "format": "date-time"},
                "createdBefore": {"type": "string", "format": "date-time"},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "shopify_list_customers",
        "description": "List Shopify customers (read-only) with orders count and amount spent.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "minimum": 1, "maximum": 1000, "default": 50},
                "query": {"type": "string", "description": "Shopify customer search query."},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "shopify_list_products",
        "description": "List Shopify products (read-only), variants, SKU, price and inventory quantity.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "minimum": 1, "maximum": 1000, "default": 50},
                "query": {"type": "string", "description": "Shopify product search query."},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "shopify_customer_purchase_summary",
        "description": "Purchase summary for one customer: total orders, total spent, products and quantities.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "customerId": {"type": "string"},
                "email": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 1000, "default": 250},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "shopify_sales_by_customer_product",
        "description": "Aggregate orders to answer who bought what and how much.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "minimum": 1, "maximum": 1000, "default": 250},
                "query": {"type": "string"},
                "createdAfter": {"type": "string", "format": "date-time"},
                "createdBefore": {"type": "string", "format": "date-time"},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "shopify_sales_overview",
        "description": "Sales KPIs for a date range, optionally compared to the previous period.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "dateFrom": {"type": "string", "format": "date-time"},
                "dateTo": {"type": "string", "format": "date-time"},
                "query": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 1000, "default": 1000},
                "comparePreviousPeriod": {"type": "boolean", "default": False},
            },
            "required": ["dateFrom", "dateTo"],
            "additionalProperties": False,
        },
    },
    {
        "name": "shopify_sales_timeseries",
        "description": "Sales time series grouped by day, week, or month.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "dateFrom": {"type": "string", "format": "date-time"},
                "dateTo": {"type": "string", "format": "date-time"},
                "query": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 1000, "default": 1000},
                "interval": {"type": "string", "enum": ["day", "week", "month"], "default": "day"},
                "comparePreviousPeriod": {"type": "boolean", "default": False},
            },
            "required": ["dateFrom", "dateTo"],
            "additionalProperties": False,
        },
    },
    {
        "name": "shopify_top_products",
        "description": "Top products or variants by net sales, gross sales, units sold, or orders.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "dateFrom": {"type": "string", "format": "date-time"},
                "dateTo": {"type": "string", "format": "date-time"},
                "query": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 1000, "default": 10},
                "sortBy": {"type": "string", "enum": ["netSales", "grossSales", "unitsSold", "orders"], "default": "netSales"},
                "groupBy": {"type": "string", "enum": ["product", "variant"], "default": "product"},
            },
            "required": ["dateFrom", "dateTo"],
            "additionalProperties": False,
        },
    },
    {
        "name": "shopify_top_customers",
        "description": "Top customers by sales or volume with optional new/returning filter.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "dateFrom": {"type": "string", "format": "date-time"},
                "dateTo": {"type": "string", "format": "date-time"},
                "query": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 1000, "default": 10},
                "sortBy": {"type": "string", "enum": ["netSales", "grossSales", "unitsSold", "orders"], "default": "netSales"},
                "customerType": {"type": "string", "enum": ["all", "new", "returning"], "default": "all"},
            },
            "required": ["dateFrom", "dateTo"],
            "additionalProperties": False,
        },
    },
    {
        "name": "shopify_discount_analysis",
        "description": "Discount totals, discounted order rate, and top discount codes for a date range.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "dateFrom": {"type": "string", "format": "date-time"},
                "dateTo": {"type": "string", "format": "date-time"},
                "query": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 1000, "default": 10},
            },
            "required": ["dateFrom", "dateTo"],
            "additionalProperties": False,
        },
    },
    {
        "name": "shopify_retention_overview",
        "description": "Retention KPIs for customers whose first order happened in the selected cohort window.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "dateFrom": {"type": "string", "format": "date-time"},
                "dateTo": {"type": "string", "format": "date-time"},
                "asOfDate": {"type": "string", "format": "date-time"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 1000, "default": 1000},
            },
            "required": ["dateFrom", "dateTo"],
            "additionalProperties": False,
        },
    },
    {
        "name": "shopify_repeat_purchase_windows",
        "description": "Repeat purchase rates for fixed 30/60/90/180-day windows.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "dateFrom": {"type": "string", "format": "date-time"},
                "dateTo": {"type": "string", "format": "date-time"},
                "asOfDate": {"type": "string", "format": "date-time"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 1000, "default": 1000},
            },
            "required": ["dateFrom", "dateTo"],
            "additionalProperties": False,
        },
    },
    {
        "name": "shopify_time_to_second_order",
        "description": "Distribution and summary stats for days between first and second order.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "dateFrom": {"type": "string", "format": "date-time"},
                "dateTo": {"type": "string", "format": "date-time"},
                "asOfDate": {"type": "string", "format": "date-time"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 1000, "default": 1000},
            },
            "required": ["dateFrom", "dateTo"],
            "additionalProperties": False,
        },
    },
    {
        "name": "shopify_inactive_customer_summary",
        "description": "Customer inactivity summary for fixed 30/60/90/180-day windows.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "asOfDate": {"type": "string", "format": "date-time"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 1000, "default": 1000},
            },
            "required": ["asOfDate"],
            "additionalProperties": False,
        },
    },
]


def _as_tool_result(payload: Any) -> dict[str, Any]:
    return {
        "content": [{"type": "text", "text": json.dumps(payload, indent=2, ensure_ascii=True)}],
        "structuredContent": payload,
    }


def call_tool(client: Any, name: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
    args = args or {}

    def _load_reporting_orders(include_previous_period: bool = False) -> list[dict[str, Any]]:
        date_from = str(args.get("dateFrom") or "")
        date_to = str(args.get("dateTo") or "")
        if not date_from or not date_to:
            raise ValueError("dateFrom and dateTo are required.")
        created_after = date_from
        if include_previous_period:
            created_after, _ = previous_period_window(date_from, date_to)
        return client.list_orders(
            limit=int(args.get("limit") or 1000),
            query=args.get("query"),
            createdAfter=created_after,
            createdBefore=date_to,
        )

    def _load_retention_orders() -> list[dict[str, Any]]:
        as_of_date = str(args.get("asOfDate") or args.get("dateTo") or "")
        if not as_of_date:
            raise ValueError("asOfDate or dateTo is required.")
        return client.list_orders(
            limit=int(args.get("limit") or 1000),
            createdBefore=as_of_date,
        )

    if name == "shopify_list_orders":
        orders = client.list_orders(**args)
        return _as_tool_result({"count": len(orders), "orders": orders})
    if name == "shopify_list_customers":
        customers = client.list_customers(**args)
        return _as_tool_result({"count": len(customers), "customers": customers})
    if name == "shopify_list_products":
        products = client.list_products(**args)
        return _as_tool_result({"count": len(products), "products": products})
    if name == "shopify_customer_purchase_summary":
        summary = client.customer_purchase_summary(**args)
        return _as_tool_result(summary)
    if name == "shopify_sales_by_customer_product":
        orders = client.list_orders(**args)
        return _as_tool_result(aggregate_by_customer_product(orders))
    if name == "shopify_sales_overview":
        orders = _load_reporting_orders(include_previous_period=bool(args.get("comparePreviousPeriod")))
        result = sales_overview(
            orders,
            date_from=args["dateFrom"],
            date_to=args["dateTo"],
            compare_previous_period=bool(args.get("comparePreviousPeriod")),
        )
        return _as_tool_result(result)
    if name == "shopify_sales_timeseries":
        orders = _load_reporting_orders(include_previous_period=bool(args.get("comparePreviousPeriod")))
        result = sales_timeseries(
            orders,
            date_from=args["dateFrom"],
            date_to=args["dateTo"],
            interval=str(args.get("interval") or "day"),
            compare_previous_period=bool(args.get("comparePreviousPeriod")),
        )
        return _as_tool_result(result)
    if name == "shopify_top_products":
        orders = _load_reporting_orders()
        result = top_products(
            orders,
            date_from=args["dateFrom"],
            date_to=args["dateTo"],
            sort_by=str(args.get("sortBy") or "netSales"),
            group_by=str(args.get("groupBy") or "product"),
            limit=int(args.get("limit") or 10),
        )
        return _as_tool_result(result)
    if name == "shopify_top_customers":
        orders = _load_reporting_orders()
        result = top_customers(
            orders,
            date_from=args["dateFrom"],
            date_to=args["dateTo"],
            sort_by=str(args.get("sortBy") or "netSales"),
            customer_type=str(args.get("customerType") or "all"),
            limit=int(args.get("limit") or 10),
        )
        return _as_tool_result(result)
    if name == "shopify_discount_analysis":
        orders = _load_reporting_orders()
        result = discount_analysis(
            orders,
            date_from=args["dateFrom"],
            date_to=args["dateTo"],
            limit=int(args.get("limit") or 10),
        )
        return _as_tool_result(result)
    if name == "shopify_retention_overview":
        orders = _load_retention_orders()
        result = retention_overview(
            orders,
            date_from=args["dateFrom"],
            date_to=args["dateTo"],
            as_of_date=args.get("asOfDate"),
        )
        return _as_tool_result(result)
    if name == "shopify_repeat_purchase_windows":
        orders = _load_retention_orders()
        result = repeat_purchase_windows(
            orders,
            date_from=args["dateFrom"],
            date_to=args["dateTo"],
            as_of_date=args.get("asOfDate"),
        )
        return _as_tool_result(result)
    if name == "shopify_time_to_second_order":
        orders = _load_retention_orders()
        result = time_to_second_order(
            orders,
            date_from=args["dateFrom"],
            date_to=args["dateTo"],
            as_of_date=args.get("asOfDate"),
        )
        return _as_tool_result(result)
    if name == "shopify_inactive_customer_summary":
        orders = _load_retention_orders()
        result = inactive_customer_summary(orders, as_of_date=args["asOfDate"])
        return _as_tool_result(result)
    raise ValueError(f"Unknown tool: {name}")

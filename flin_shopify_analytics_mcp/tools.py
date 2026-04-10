"""MCP tool declarations and dispatch."""

from __future__ import annotations

import json
from typing import Any

from .analytics import aggregate_by_customer_product


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
]


def _as_tool_result(payload: Any) -> dict[str, Any]:
    return {
        "content": [{"type": "text", "text": json.dumps(payload, indent=2, ensure_ascii=True)}],
        "structuredContent": payload,
    }


def call_tool(client: Any, name: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
    args = args or {}
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
    raise ValueError(f"Unknown tool: {name}")

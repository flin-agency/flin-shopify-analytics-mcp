"""Analytics helpers for customer/product aggregation."""

from __future__ import annotations

from typing import Any


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _customer_key(customer: dict[str, Any] | None) -> str:
    if customer and customer.get("id"):
        return str(customer["id"])
    if customer and customer.get("email"):
        return f"email:{customer['email']}"
    return "guest"


def aggregate_by_customer_product(orders: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate orders to answer who bought what and how much."""
    customers: dict[str, dict[str, Any]] = {}

    for order in orders:
        customer = order.get("customer") or {}
        key = _customer_key(customer)
        entry = customers.setdefault(
            key,
            {
                "customerId": customer.get("id"),
                "customerName": customer.get("name") or "Guest",
                "customerEmail": customer.get("email"),
                "totalOrders": 0,
                "totalSpent": 0.0,
                "currencyCode": order.get("currencyCode"),
                "products": {},
            },
        )

        entry["totalOrders"] += 1
        entry["totalSpent"] += _to_float(order.get("totalAmount"))
        if not entry.get("currencyCode") and order.get("currencyCode"):
            entry["currencyCode"] = order["currencyCode"]

        for item in order.get("items", []):
            product_key = item.get("productId") or f"{item.get('title')}:{item.get('sku') or ''}"
            product = entry["products"].setdefault(
                product_key,
                {
                    "productId": item.get("productId"),
                    "title": item.get("title") or "Unknown product",
                    "sku": item.get("sku"),
                    "quantity": 0,
                },
            )
            product["quantity"] += int(item.get("quantity") or 0)

    customer_rows: list[dict[str, Any]] = []
    for entry in customers.values():
        products = sorted(entry["products"].values(), key=lambda row: row["quantity"], reverse=True)
        customer_rows.append(
            {
                "customerId": entry["customerId"],
                "customerName": entry["customerName"],
                "customerEmail": entry["customerEmail"],
                "totalOrders": entry["totalOrders"],
                "totalSpent": round(entry["totalSpent"], 2),
                "currencyCode": entry["currencyCode"],
                "products": products,
            }
        )

    customer_rows.sort(key=lambda row: row["totalSpent"], reverse=True)
    return {
        "orderCount": len(orders),
        "customerCount": len(customer_rows),
        "customers": customer_rows,
    }

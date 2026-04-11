"""Analytics helpers for reporting and customer/product aggregation."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _parse_datetime(value: str) -> datetime:
    text = value.strip()
    if text.endswith("Z"):
        return datetime.fromisoformat(text[:-1]).replace(tzinfo=UTC)
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _normalize_datetime(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        return value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)
    return _parse_datetime(value)


def _customer_key(customer: dict[str, Any] | None) -> str:
    if customer and customer.get("id"):
        return str(customer["id"])
    if customer and customer.get("email"):
        return f"email:{customer['email']}"
    return "guest"


def _round_money(value: float) -> float:
    return round(value, 2)


def _is_new_customer(order: dict[str, Any]) -> bool:
    customer = order.get("customer") or {}
    return int(customer.get("numberOfOrders") or 0) == 1


def _filtered_orders(orders: list[dict[str, Any]], date_from: str, date_to: str) -> list[dict[str, Any]]:
    start = _normalize_datetime(date_from)
    end = _normalize_datetime(date_to)
    filtered: list[dict[str, Any]] = []
    for order in orders:
        created_at = order.get("createdAt")
        if not created_at:
            continue
        created_dt = _normalize_datetime(created_at)
        if start <= created_dt <= end:
            filtered.append(order)
    return filtered


def _previous_period(date_from: str, date_to: str) -> tuple[str, str]:
    start = _normalize_datetime(date_from)
    end = _normalize_datetime(date_to)
    duration = end - start
    previous_end = start - timedelta(seconds=1)
    previous_start = previous_end - duration
    return (
        previous_start.isoformat().replace("+00:00", "Z"),
        previous_end.isoformat().replace("+00:00", "Z"),
    )


def previous_period_window(date_from: str, date_to: str) -> tuple[str, str]:
    return _previous_period(date_from, date_to)


def _overview_metrics(orders: list[dict[str, Any]]) -> dict[str, Any]:
    gross_sales = sum(_to_float(order.get("grossSales")) for order in orders)
    discount_amount = sum(_to_float(order.get("discountAmount")) for order in orders)
    refunded_amount = sum(_to_float(order.get("refundedAmount")) for order in orders)
    net_sales = sum(_to_float(order.get("netSales")) for order in orders)
    units_sold = sum(int(order.get("unitsSold") or 0) for order in orders)
    order_count = len(orders)
    average_order_value = net_sales / order_count if order_count else 0.0
    new_customer_orders = sum(1 for order in orders if _is_new_customer(order))
    returning_customer_orders = order_count - new_customer_orders
    currencies = [order.get("currencyCode") for order in orders if order.get("currencyCode")]
    return {
        "orders": order_count,
        "unitsSold": units_sold,
        "grossSales": _round_money(gross_sales),
        "discountAmount": _round_money(discount_amount),
        "refundedAmount": _round_money(refunded_amount),
        "netSales": _round_money(net_sales),
        "averageOrderValue": _round_money(average_order_value),
        "newCustomerOrders": new_customer_orders,
        "returningCustomerOrders": returning_customer_orders,
        "currencyCode": currencies[0] if currencies else None,
    }


def _delta_metrics(current: dict[str, Any], previous: dict[str, Any]) -> dict[str, Any]:
    delta: dict[str, Any] = {}
    for key in [
        "orders",
        "unitsSold",
        "grossSales",
        "discountAmount",
        "refundedAmount",
        "netSales",
        "averageOrderValue",
        "newCustomerOrders",
        "returningCustomerOrders",
    ]:
        current_value = current.get(key, 0)
        previous_value = previous.get(key, 0)
        value = current_value - previous_value
        delta[key] = _round_money(value) if isinstance(value, float) else value
    return delta


def sales_overview(
    orders: list[dict[str, Any]],
    *,
    date_from: str,
    date_to: str,
    compare_previous_period: bool = False,
) -> dict[str, Any]:
    current_orders = _filtered_orders(orders, date_from, date_to)
    current_period = _overview_metrics(current_orders)
    result: dict[str, Any] = {
        "dateFrom": date_from,
        "dateTo": date_to,
        "currentPeriod": current_period,
    }
    if compare_previous_period:
        previous_from, previous_to = _previous_period(date_from, date_to)
        previous_orders = _filtered_orders(orders, previous_from, previous_to)
        previous_period = _overview_metrics(previous_orders)
        result["previousPeriod"] = previous_period
        result["delta"] = _delta_metrics(current_period, previous_period)
    return result


def _bucket_key(created_at: str, interval: str) -> tuple[str, datetime]:
    created_dt = _normalize_datetime(created_at)
    if interval == "day":
        label = created_dt.strftime("%Y-%m-%d")
        anchor = created_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        return label, anchor
    if interval == "week":
        week_start = (created_dt - timedelta(days=created_dt.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        return week_start.strftime("%Y-%m-%d"), week_start
    if interval == "month":
        month_start = created_dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return month_start.strftime("%Y-%m"), month_start
    raise ValueError("interval must be one of: day, week, month")


def _timeseries_buckets(orders: list[dict[str, Any]], interval: str) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}
    for order in orders:
        created_at = order.get("createdAt")
        if not created_at:
            continue
        label, anchor = _bucket_key(created_at, interval)
        entry = buckets.setdefault(
            label,
            {
                "label": label,
                "anchor": anchor,
                "orders": 0,
                "unitsSold": 0,
                "grossSales": 0.0,
                "discountAmount": 0.0,
                "refundedAmount": 0.0,
                "netSales": 0.0,
            },
        )
        entry["orders"] += 1
        entry["unitsSold"] += int(order.get("unitsSold") or 0)
        entry["grossSales"] += _to_float(order.get("grossSales"))
        entry["discountAmount"] += _to_float(order.get("discountAmount"))
        entry["refundedAmount"] += _to_float(order.get("refundedAmount"))
        entry["netSales"] += _to_float(order.get("netSales"))

    rows = sorted(buckets.values(), key=lambda row: row["anchor"])
    output: list[dict[str, Any]] = []
    for row in rows:
        orders_count = row["orders"]
        output.append(
            {
                "label": row["label"],
                "orders": orders_count,
                "unitsSold": row["unitsSold"],
                "grossSales": _round_money(row["grossSales"]),
                "discountAmount": _round_money(row["discountAmount"]),
                "refundedAmount": _round_money(row["refundedAmount"]),
                "netSales": _round_money(row["netSales"]),
                "averageOrderValue": _round_money(row["netSales"] / orders_count if orders_count else 0.0),
            }
        )
    return output


def sales_timeseries(
    orders: list[dict[str, Any]],
    *,
    date_from: str,
    date_to: str,
    interval: str,
    compare_previous_period: bool = False,
) -> dict[str, Any]:
    current_orders = _filtered_orders(orders, date_from, date_to)
    result: dict[str, Any] = {
        "dateFrom": date_from,
        "dateTo": date_to,
        "interval": interval,
        "buckets": _timeseries_buckets(current_orders, interval),
    }
    if compare_previous_period:
        previous_from, previous_to = _previous_period(date_from, date_to)
        previous_orders = _filtered_orders(orders, previous_from, previous_to)
        result["previousPeriod"] = {
            "dateFrom": previous_from,
            "dateTo": previous_to,
            "buckets": _timeseries_buckets(previous_orders, interval),
        }
    return result


def top_products(
    orders: list[dict[str, Any]],
    *,
    date_from: str,
    date_to: str,
    sort_by: str = "netSales",
    group_by: str = "product",
    limit: int = 10,
) -> dict[str, Any]:
    grouped: dict[str, dict[str, Any]] = {}
    for order in _filtered_orders(orders, date_from, date_to):
        for item in order.get("items") or []:
            if group_by == "variant":
                key = item.get("variantId") or f"{item.get('productId')}:{item.get('variantTitle')}"
            elif group_by == "product":
                key = item.get("productId") or f"{item.get('title')}:{item.get('sku') or ''}"
            else:
                raise ValueError("groupBy must be one of: product, variant")
            row = grouped.setdefault(
                key,
                {
                    "productId": item.get("productId"),
                    "variantId": item.get("variantId"),
                    "title": item.get("title"),
                    "variantTitle": item.get("variantTitle"),
                    "sku": item.get("sku"),
                    "orders": 0,
                    "unitsSold": 0,
                    "grossSales": 0.0,
                    "discountAmount": 0.0,
                    "netSales": 0.0,
                },
            )
            row["orders"] += 1
            row["unitsSold"] += int(item.get("currentQuantity") or item.get("quantity") or 0)
            row["grossSales"] += _to_float(item.get("grossSales"))
            row["discountAmount"] += _to_float(item.get("discountAmount"))
            row["netSales"] += _to_float(item.get("netSales"))

    sort_key = sort_by
    if sort_key not in {"netSales", "grossSales", "unitsSold", "orders"}:
        raise ValueError("sortBy must be one of: netSales, grossSales, unitsSold, orders")
    rows = sorted(grouped.values(), key=lambda row: row[sort_key], reverse=True)
    output = []
    for row in rows[: max(1, int(limit or 10))]:
        output.append(
            {
                **row,
                "grossSales": _round_money(row["grossSales"]),
                "discountAmount": _round_money(row["discountAmount"]),
                "netSales": _round_money(row["netSales"]),
            }
        )
    return {"dateFrom": date_from, "dateTo": date_to, "sortBy": sort_by, "groupBy": group_by, "rows": output}


def top_customers(
    orders: list[dict[str, Any]],
    *,
    date_from: str,
    date_to: str,
    sort_by: str = "netSales",
    customer_type: str = "all",
    limit: int = 10,
) -> dict[str, Any]:
    grouped: dict[str, dict[str, Any]] = {}
    for order in _filtered_orders(orders, date_from, date_to):
        is_new = _is_new_customer(order)
        if customer_type == "new" and not is_new:
            continue
        if customer_type == "returning" and is_new:
            continue
        if customer_type not in {"all", "new", "returning"}:
            raise ValueError("customerType must be one of: all, new, returning")

        customer = order.get("customer") or {}
        key = _customer_key(customer)
        row = grouped.setdefault(
            key,
            {
                "customerId": customer.get("id"),
                "customerName": customer.get("name") or "Guest",
                "customerEmail": customer.get("email"),
                "customerType": "new" if is_new else "returning",
                "orders": 0,
                "unitsSold": 0,
                "grossSales": 0.0,
                "discountAmount": 0.0,
                "refundedAmount": 0.0,
                "netSales": 0.0,
            },
        )
        row["orders"] += 1
        row["unitsSold"] += int(order.get("unitsSold") or 0)
        row["grossSales"] += _to_float(order.get("grossSales"))
        row["discountAmount"] += _to_float(order.get("discountAmount"))
        row["refundedAmount"] += _to_float(order.get("refundedAmount"))
        row["netSales"] += _to_float(order.get("netSales"))

    sort_key = sort_by
    if sort_key not in {"netSales", "grossSales", "unitsSold", "orders"}:
        raise ValueError("sortBy must be one of: netSales, grossSales, unitsSold, orders")
    rows = sorted(grouped.values(), key=lambda row: row[sort_key], reverse=True)
    output = []
    for row in rows[: max(1, int(limit or 10))]:
        output.append(
            {
                **row,
                "grossSales": _round_money(row["grossSales"]),
                "discountAmount": _round_money(row["discountAmount"]),
                "refundedAmount": _round_money(row["refundedAmount"]),
                "netSales": _round_money(row["netSales"]),
            }
        )
    return {"dateFrom": date_from, "dateTo": date_to, "sortBy": sort_by, "customerType": customer_type, "rows": output}


def discount_analysis(
    orders: list[dict[str, Any]],
    *,
    date_from: str,
    date_to: str,
    limit: int = 10,
) -> dict[str, Any]:
    filtered_orders = _filtered_orders(orders, date_from, date_to)
    discounted_orders = [order for order in filtered_orders if _to_float(order.get("discountAmount")) > 0]
    total_discount = sum(_to_float(order.get("discountAmount")) for order in filtered_orders)
    code_totals: dict[str, dict[str, Any]] = {}
    for order in discounted_orders:
        codes = order.get("discountCodes") or []
        if not codes:
            codes = ["<no_code>"]
        for code in codes:
            entry = code_totals.setdefault(code, {"code": code, "orders": 0, "discountAmount": 0.0})
            entry["orders"] += 1
            entry["discountAmount"] += _to_float(order.get("discountAmount"))

    top_codes = sorted(code_totals.values(), key=lambda row: row["discountAmount"], reverse=True)
    rows = [
        {
            "code": row["code"],
            "orders": row["orders"],
            "discountAmount": _round_money(row["discountAmount"]),
        }
        for row in top_codes[: max(1, int(limit or 10))]
    ]
    order_count = len(filtered_orders)
    discounted_order_count = len(discounted_orders)
    return {
        "dateFrom": date_from,
        "dateTo": date_to,
        "orderCount": order_count,
        "discountedOrders": discounted_order_count,
        "discountedOrderRate": discounted_order_count / order_count if order_count else 0.0,
        "discountAmountTotal": _round_money(total_discount),
        "averageDiscountPerDiscountedOrder": _round_money(
            total_discount / discounted_order_count if discounted_order_count else 0.0
        ),
        "topDiscountCodes": rows,
    }


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

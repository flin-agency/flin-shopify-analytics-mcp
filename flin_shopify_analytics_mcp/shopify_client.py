"""Shopify GraphQL client with read-only guard and dual auth modes."""

from __future__ import annotations

import json
import ssl
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import certifi

from .analytics import aggregate_by_customer_product
from .config import Config


ORDERS_QUERY = """
query ListOrders($first: Int!, $after: String, $query: String) {
  orders(first: $first, after: $after, query: $query, sortKey: CREATED_AT, reverse: true) {
    edges {
      cursor
      node {
        id
        name
        createdAt
        totalPriceSet {
          shopMoney {
            amount
            currencyCode
          }
        }
        customer {
          id
          displayName
          email
        }
        lineItems(first: 100) {
          edges {
            node {
              title
              sku
              quantity
              variantTitle
              product {
                id
                title
              }
            }
          }
        }
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""

CUSTOMERS_QUERY = """
query ListCustomers($first: Int!, $after: String, $query: String) {
  customers(first: $first, after: $after, query: $query, sortKey: UPDATED_AT, reverse: true) {
    edges {
      cursor
      node {
        id
        displayName
        email
        createdAt
        state
        ordersCount
        amountSpent {
          amount
          currencyCode
        }
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""

PRODUCTS_QUERY = """
query ListProducts($first: Int!, $after: String, $query: String) {
  products(first: $first, after: $after, query: $query, sortKey: UPDATED_AT, reverse: true) {
    edges {
      cursor
      node {
        id
        title
        handle
        vendor
        productType
        status
        createdAt
        variants(first: 50) {
          edges {
            node {
              id
              title
              sku
              price
              inventoryQuantity
            }
          }
        }
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""

CUSTOMER_ORDERS_QUERY = """
query CustomerOrders($id: ID!, $first: Int!, $after: String) {
  customer(id: $id) {
    id
    displayName
    email
    amountSpent {
      amount
      currencyCode
    }
    orders(first: $first, after: $after, sortKey: CREATED_AT, reverse: true) {
      edges {
        cursor
        node {
          id
          name
          createdAt
          totalPriceSet {
            shopMoney {
              amount
              currencyCode
            }
          }
          lineItems(first: 100) {
            edges {
              node {
                title
                sku
                quantity
                variantTitle
                product {
                  id
                  title
                }
              }
            }
          }
        }
      }
      pageInfo {
        hasNextPage
        endCursor
      }
    }
  }
}
"""


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _to_int(value: Any, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    if parsed <= 0:
        return default
    return parsed


def _quote_search_value(value: str) -> str:
    if all(ch.isalnum() or ch in "._:@-" for ch in value):
        return value
    return '"' + value.replace('"', '\\"') + '"'


def _normalize_iso_datetime(value: str) -> str:
    text = value.strip()
    if text.endswith("Z"):
        dt = datetime.fromisoformat(text[:-1]).replace(tzinfo=UTC)
    else:
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        else:
            dt = dt.astimezone(UTC)
    return dt.isoformat().replace("+00:00", "Z")


def _build_order_search_query(
    query: str | None, created_after: str | None, created_before: str | None
) -> str | None:
    filters: list[str] = []
    if query and query.strip():
        filters.append(query.strip())
    if created_after:
        filters.append(f"created_at:>={_normalize_iso_datetime(created_after)}")
    if created_before:
        filters.append(f"created_at:<={_normalize_iso_datetime(created_before)}")
    joined = " ".join(filters).strip()
    return joined or None


def _map_line_item(node: dict[str, Any]) -> dict[str, Any]:
    product = node.get("product") or {}
    return {
        "productId": product.get("id"),
        "title": product.get("title") or node.get("title"),
        "sku": node.get("sku"),
        "variantTitle": node.get("variantTitle"),
        "quantity": int(node.get("quantity") or 0),
    }


def _map_order_node(node: dict[str, Any]) -> dict[str, Any]:
    total_set = (node.get("totalPriceSet") or {}).get("shopMoney") or {}
    customer = node.get("customer")
    line_items = ((node.get("lineItems") or {}).get("edges") or [])
    return {
        "id": node.get("id"),
        "name": node.get("name"),
        "createdAt": node.get("createdAt"),
        "totalAmount": _to_float(total_set.get("amount")),
        "currencyCode": total_set.get("currencyCode"),
        "customer": {
            "id": customer.get("id"),
            "name": customer.get("displayName"),
            "email": customer.get("email"),
        }
        if customer
        else None,
        "items": [_map_line_item(edge.get("node") or {}) for edge in line_items],
    }


def _map_customer_node(node: dict[str, Any]) -> dict[str, Any]:
    amount_spent = node.get("amountSpent") or {}
    return {
        "id": node.get("id"),
        "displayName": node.get("displayName"),
        "email": node.get("email"),
        "createdAt": node.get("createdAt"),
        "state": node.get("state"),
        "ordersCount": int(node.get("ordersCount") or 0),
        "amountSpent": _to_float(amount_spent.get("amount")),
        "currencyCode": amount_spent.get("currencyCode"),
    }


def _map_product_node(node: dict[str, Any]) -> dict[str, Any]:
    variants = ((node.get("variants") or {}).get("edges") or [])
    return {
        "id": node.get("id"),
        "title": node.get("title"),
        "handle": node.get("handle"),
        "vendor": node.get("vendor"),
        "productType": node.get("productType"),
        "status": node.get("status"),
        "createdAt": node.get("createdAt"),
        "variants": [
            {
                "id": edge.get("node", {}).get("id"),
                "title": edge.get("node", {}).get("title"),
                "sku": edge.get("node", {}).get("sku"),
                "price": _to_float(edge.get("node", {}).get("price")),
                "inventoryQuantity": int(edge.get("node", {}).get("inventoryQuantity") or 0),
            }
            for edge in variants
        ],
    }


@dataclass
class HttpResponse:
    status: int
    payload: dict[str, Any] | None
    status_text: str


HttpPostFn = Callable[[str, dict[str, str], bytes], HttpResponse]


def _resolve_ca_bundle_path(config: Config) -> str | None:
    return config.ca_bundle_path or certifi.where()


def _is_ssl_error(error: BaseException) -> bool:
    if isinstance(error, ssl.SSLError):
        return True
    reason = getattr(error, "reason", None)
    if isinstance(reason, ssl.SSLError):
        return True
    return "CERTIFICATE_VERIFY_FAILED" in str(error)


def _ssl_error_message(ca_bundle_path: str | None) -> str:
    detail = f" Current CA bundle: {ca_bundle_path}." if ca_bundle_path else ""
    return (
        "SSL certificate verification failed while connecting to Shopify."
        " Ensure the Python environment has a valid CA bundle or set SHOPIFY_CA_BUNDLE / SSL_CERT_FILE."
        f"{detail}"
    )


def _build_post_json(config: Config) -> HttpPostFn:
    ca_bundle_path = _resolve_ca_bundle_path(config)
    ssl_context = ssl.create_default_context(cafile=ca_bundle_path) if ca_bundle_path else ssl.create_default_context()

    def _post_json(url: str, headers: dict[str, str], body: bytes) -> HttpResponse:
        request = Request(url=url, data=body, headers=headers, method="POST")
        try:
            with urlopen(request, timeout=30, context=ssl_context) as response:
                raw = response.read().decode("utf-8")
                payload = json.loads(raw) if raw else None
                status = int(response.status)
                reason = getattr(response, "reason", "OK")
                return HttpResponse(status=status, payload=payload, status_text=str(reason))
        except HTTPError as error:
            raw = error.read().decode("utf-8")
            payload = json.loads(raw) if raw else None
            return HttpResponse(status=error.code, payload=payload, status_text=str(error.reason))
        except URLError as error:
            if _is_ssl_error(error):
                raise RuntimeError(_ssl_error_message(ca_bundle_path)) from error
            raise

    return _post_json


class ShopifyClient:
    """Shopify GraphQL client for read-only analytics."""

    def __init__(self, config: Config, post_json: HttpPostFn | None = None):
        self.config = config
        self.post_json = post_json or _build_post_json(config)
        self.endpoint = f"https://{config.store_domain}/admin/api/{config.api_version}/graphql.json"
        self.oauth_token_endpoint = f"https://{config.store_domain}/admin/oauth/access_token"
        self.cached_token: str | None = None
        self.cached_token_expires_at: float = 0.0

    def invalidate_cached_token(self) -> None:
        self.cached_token = None
        self.cached_token_expires_at = 0.0

    def _token_is_valid(self) -> bool:
        if not self.cached_token or self.cached_token_expires_at <= 0:
            return False
        skew = float(self.config.oauth_refresh_skew_seconds)
        return time.time() < (self.cached_token_expires_at - skew)

    def _exchange_client_credentials_token(self) -> str:
        body = urlencode(
            {
                "grant_type": "client_credentials",
                "client_id": self.config.client_id or "",
                "client_secret": self.config.client_secret or "",
            }
        ).encode("utf-8")
        response = self.post_json(
            self.oauth_token_endpoint,
            {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            },
            body,
        )
        if response.status < 200 or response.status >= 300:
            raise RuntimeError(
                f"Shopify OAuth token request failed ({response.status}): {self._error_details(response)}"
            )
        payload = response.payload or {}
        access_token = payload.get("access_token")
        if not access_token:
            raise RuntimeError("Shopify OAuth token response missing access_token.")

        fallback_ttl = _to_int(
            self.config.oauth_token_ttl_fallback_seconds,
            self.config.oauth_token_ttl_fallback_seconds,
        )
        expires_in = _to_int(payload.get("expires_in"), fallback_ttl)
        self.cached_token = str(access_token)
        self.cached_token_expires_at = time.time() + float(expires_in)
        return self.cached_token

    def _get_access_token(self) -> str:
        if self.config.auth_mode == "static_token":
            if not self.config.static_access_token:
                raise RuntimeError("Static token mode enabled but no token configured.")
            return self.config.static_access_token

        if self.config.auth_mode != "client_credentials":
            raise RuntimeError(f"Unsupported auth mode: {self.config.auth_mode}")

        if self._token_is_valid():
            return self.cached_token or ""
        return self._exchange_client_credentials_token()

    @staticmethod
    def _error_details(response: HttpResponse) -> str:
        payload = response.payload or {}
        if payload.get("errors") is not None:
            return json.dumps(payload["errors"], ensure_ascii=True)
        if payload.get("error_description"):
            return str(payload["error_description"])
        if payload.get("error"):
            return str(payload["error"])
        return response.status_text

    def graphql(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        if "mutation" in query.lower():
            raise RuntimeError("Read-only mode enabled: GraphQL mutations are blocked.")

        def _run() -> HttpResponse:
            token = self._get_access_token()
            body = json.dumps({"query": query, "variables": variables or {}}).encode("utf-8")
            return self.post_json(
                self.endpoint,
                {
                    "Content-Type": "application/json",
                    "X-Shopify-Access-Token": token,
                },
                body,
            )

        response = _run()
        if response.status == 401 and self.config.auth_mode == "client_credentials":
            self.invalidate_cached_token()
            response = _run()

        if response.status < 200 or response.status >= 300:
            raise RuntimeError(
                f"Shopify API request failed ({response.status}): {self._error_details(response)}"
            )

        payload = response.payload or {}
        errors = payload.get("errors") or []
        if errors:
            raise RuntimeError(f"Shopify GraphQL errors: {json.dumps(errors, ensure_ascii=True)}")

        return payload.get("data") or {}

    def list_orders(
        self,
        limit: int = 50,
        query: str | None = None,
        createdAfter: str | None = None,
        createdBefore: str | None = None,
    ) -> list[dict[str, Any]]:
        capped_limit = max(1, min(int(limit or 50), 1000))
        search_query = _build_order_search_query(query, createdAfter, createdBefore)
        orders: list[dict[str, Any]] = []
        after: str | None = None
        has_next_page = True

        while len(orders) < capped_limit and has_next_page:
            first = min(250, capped_limit - len(orders))
            data = self.graphql(ORDERS_QUERY, {"first": first, "after": after, "query": search_query})
            orders_data = data.get("orders") or {}
            edges = orders_data.get("edges") or []
            for edge in edges:
                orders.append(_map_order_node(edge.get("node") or {}))
            page_info = orders_data.get("pageInfo") or {}
            has_next_page = bool(page_info.get("hasNextPage"))
            after = page_info.get("endCursor")

        return orders

    def list_customers(self, limit: int = 50, query: str | None = None) -> list[dict[str, Any]]:
        capped_limit = max(1, min(int(limit or 50), 1000))
        customers: list[dict[str, Any]] = []
        after: str | None = None
        has_next_page = True

        while len(customers) < capped_limit and has_next_page:
            first = min(250, capped_limit - len(customers))
            data = self.graphql(CUSTOMERS_QUERY, {"first": first, "after": after, "query": query})
            customers_data = data.get("customers") or {}
            edges = customers_data.get("edges") or []
            for edge in edges:
                customers.append(_map_customer_node(edge.get("node") or {}))
            page_info = customers_data.get("pageInfo") or {}
            has_next_page = bool(page_info.get("hasNextPage"))
            after = page_info.get("endCursor")

        return customers

    def list_products(self, limit: int = 50, query: str | None = None) -> list[dict[str, Any]]:
        capped_limit = max(1, min(int(limit or 50), 1000))
        products: list[dict[str, Any]] = []
        after: str | None = None
        has_next_page = True

        while len(products) < capped_limit and has_next_page:
            first = min(250, capped_limit - len(products))
            data = self.graphql(PRODUCTS_QUERY, {"first": first, "after": after, "query": query})
            products_data = data.get("products") or {}
            edges = products_data.get("edges") or []
            for edge in edges:
                products.append(_map_product_node(edge.get("node") or {}))
            page_info = products_data.get("pageInfo") or {}
            has_next_page = bool(page_info.get("hasNextPage"))
            after = page_info.get("endCursor")

        return products

    def _resolve_customer_id(self, customer_id: str | None, email: str | None) -> str:
        if customer_id and customer_id.strip():
            return customer_id.strip()
        if not email or not email.strip():
            raise RuntimeError("Either customerId or email is required.")

        customers = self.list_customers(limit=1, query=f"email:{_quote_search_value(email.strip())}")
        if not customers:
            raise RuntimeError(f"No customer found for email: {email}")
        return str(customers[0]["id"])

    def customer_purchase_summary(
        self, customerId: str | None = None, email: str | None = None, limit: int = 250
    ) -> dict[str, Any]:
        resolved_customer_id = self._resolve_customer_id(customerId, email)
        capped_limit = max(1, min(int(limit or 250), 1000))
        orders: list[dict[str, Any]] = []
        after: str | None = None
        has_next_page = True
        customer: dict[str, Any] | None = None

        while len(orders) < capped_limit and has_next_page:
            first = min(250, capped_limit - len(orders))
            data = self.graphql(
                CUSTOMER_ORDERS_QUERY,
                {
                    "id": resolved_customer_id,
                    "first": first,
                    "after": after,
                },
            )
            customer_data = data.get("customer")
            if not customer_data:
                raise RuntimeError(f"Customer not found: {resolved_customer_id}")

            amount_spent = customer_data.get("amountSpent") or {}
            customer = {
                "id": customer_data.get("id"),
                "name": customer_data.get("displayName"),
                "email": customer_data.get("email"),
                "amountSpent": _to_float(amount_spent.get("amount")),
                "currencyCode": amount_spent.get("currencyCode"),
            }

            orders_data = customer_data.get("orders") or {}
            edges = orders_data.get("edges") or []
            for edge in edges:
                order = _map_order_node(edge.get("node") or {})
                order["customer"] = {
                    "id": customer.get("id"),
                    "name": customer.get("name"),
                    "email": customer.get("email"),
                }
                orders.append(order)

            page_info = orders_data.get("pageInfo") or {}
            has_next_page = bool(page_info.get("hasNextPage"))
            after = page_info.get("endCursor")

        aggregate = aggregate_by_customer_product(orders)
        aggregate_customer = aggregate["customers"][0] if aggregate["customers"] else None
        return {
            "customer": {
                "id": customer.get("id") if customer else resolved_customer_id,
                "name": customer.get("name") if customer else None,
                "email": customer.get("email") if customer else None,
            },
            "totalOrders": aggregate_customer["totalOrders"] if aggregate_customer else 0,
            "totalSpent": aggregate_customer["totalSpent"] if aggregate_customer else 0,
            "currencyCode": (
                aggregate_customer.get("currencyCode") if aggregate_customer else customer.get("currencyCode")
            )
            if customer
            else None,
            "products": aggregate_customer["products"] if aggregate_customer else [],
        }

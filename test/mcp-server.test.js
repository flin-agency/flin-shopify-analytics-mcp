import test from "node:test";
import assert from "node:assert/strict";

import { ShopifyAnalyticsMcpServer } from "../src/mcp-server.js";

class FakeShopifyClient {
  async listOrders() {
    return [
      {
        id: "gid://shopify/Order/1",
        name: "#1001",
        createdAt: "2026-04-10T10:00:00Z",
        totalAmount: 100,
        currencyCode: "USD",
        customer: {
          id: "gid://shopify/Customer/42",
          name: "Alice",
          email: "alice@example.com"
        },
        items: [{ productId: "gid://shopify/Product/5", title: "Shirt", sku: "SHIRT-1", quantity: 2 }]
      }
    ];
  }

  async listCustomers() {
    return [{ id: "gid://shopify/Customer/42", displayName: "Alice", email: "alice@example.com" }];
  }

  async listProducts() {
    return [{ id: "gid://shopify/Product/5", title: "Shirt", handle: "shirt" }];
  }

  async customerPurchaseSummary() {
    return {
      customer: { id: "gid://shopify/Customer/42", name: "Alice", email: "alice@example.com" },
      totalOrders: 1,
      totalSpent: 100,
      currencyCode: "USD",
      products: [{ productId: "gid://shopify/Product/5", title: "Shirt", sku: "SHIRT-1", quantity: 2 }]
    };
  }
}

test("initialize returns MCP capabilities", async () => {
  const server = new ShopifyAnalyticsMcpServer({ client: new FakeShopifyClient() });
  const response = await server.handleMessage({
    jsonrpc: "2.0",
    id: 1,
    method: "initialize",
    params: { protocolVersion: "2025-03-26" }
  });

  assert.equal(response.result.protocolVersion, "2025-03-26");
  assert.ok(response.result.capabilities.tools);
});

test("tools/list returns read-only tools", async () => {
  const server = new ShopifyAnalyticsMcpServer({ client: new FakeShopifyClient() });
  await server.handleMessage({
    jsonrpc: "2.0",
    id: 99,
    method: "initialize",
    params: { protocolVersion: "2025-03-26" }
  });
  const response = await server.handleMessage({
    jsonrpc: "2.0",
    id: 1,
    method: "tools/list",
    params: {}
  });

  const names = response.result.tools.map((tool) => tool.name);
  assert.deepEqual(names, [
    "shopify_list_orders",
    "shopify_list_customers",
    "shopify_list_products",
    "shopify_customer_purchase_summary",
    "shopify_sales_by_customer_product"
  ]);
});

test("tools/call for customer/product sales aggregation returns structured output", async () => {
  const server = new ShopifyAnalyticsMcpServer({ client: new FakeShopifyClient() });
  await server.handleMessage({
    jsonrpc: "2.0",
    id: 99,
    method: "initialize",
    params: { protocolVersion: "2025-03-26" }
  });
  const response = await server.handleMessage({
    jsonrpc: "2.0",
    id: 2,
    method: "tools/call",
    params: {
      name: "shopify_sales_by_customer_product",
      arguments: { limit: 10 }
    }
  });

  assert.equal(response.result.structuredContent.orderCount, 1);
  assert.equal(response.result.structuredContent.customers[0].products[0].quantity, 2);
});

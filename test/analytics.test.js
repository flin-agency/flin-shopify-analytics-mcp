import test from "node:test";
import assert from "node:assert/strict";

import { aggregateByCustomerProduct } from "../src/analytics.js";

test("aggregateByCustomerProduct groups quantities and spend by customer", () => {
  const orders = [
    {
      id: "gid://shopify/Order/1",
      totalAmount: 100,
      currencyCode: "USD",
      customer: {
        id: "gid://shopify/Customer/10",
        name: "Alice",
        email: "alice@example.com"
      },
      items: [
        { productId: "gid://shopify/Product/500", title: "T-Shirt", sku: "TS-1", quantity: 2 },
        { productId: "gid://shopify/Product/600", title: "Cap", sku: "CAP-1", quantity: 1 }
      ]
    },
    {
      id: "gid://shopify/Order/2",
      totalAmount: 50,
      currencyCode: "USD",
      customer: {
        id: "gid://shopify/Customer/10",
        name: "Alice",
        email: "alice@example.com"
      },
      items: [{ productId: "gid://shopify/Product/500", title: "T-Shirt", sku: "TS-1", quantity: 1 }]
    }
  ];

  const result = aggregateByCustomerProduct(orders);

  assert.equal(result.orderCount, 2);
  assert.equal(result.customerCount, 1);
  assert.equal(result.customers[0].totalOrders, 2);
  assert.equal(result.customers[0].totalSpent, 150);
  assert.deepEqual(result.customers[0].products, [
    { productId: "gid://shopify/Product/500", title: "T-Shirt", sku: "TS-1", quantity: 3 },
    { productId: "gid://shopify/Product/600", title: "Cap", sku: "CAP-1", quantity: 1 }
  ]);
});

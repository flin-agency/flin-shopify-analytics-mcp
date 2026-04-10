import { aggregateByCustomerProduct } from "./analytics.js";

function createTextResult(payload) {
  return {
    content: [{ type: "text", text: JSON.stringify(payload, null, 2) }],
    structuredContent: payload
  };
}

export const TOOL_DEFINITIONS = [
  {
    name: "shopify_list_orders",
    description:
      "List read-only Shopify orders with customer, amount and line items. Supports date window + Shopify query syntax.",
    inputSchema: {
      type: "object",
      properties: {
        limit: {
          type: "integer",
          minimum: 1,
          maximum: 1000,
          default: 50
        },
        query: {
          type: "string",
          description: "Shopify order search query."
        },
        createdAfter: {
          type: "string",
          format: "date-time",
          description: "ISO date/time. Example: 2026-01-01T00:00:00Z"
        },
        createdBefore: {
          type: "string",
          format: "date-time",
          description: "ISO date/time. Example: 2026-01-31T23:59:59Z"
        }
      },
      additionalProperties: false
    }
  },
  {
    name: "shopify_list_customers",
    description: "List Shopify customers (read-only) with orders count and amount spent.",
    inputSchema: {
      type: "object",
      properties: {
        limit: {
          type: "integer",
          minimum: 1,
          maximum: 1000,
          default: 50
        },
        query: {
          type: "string",
          description: "Shopify customer search query."
        }
      },
      additionalProperties: false
    }
  },
  {
    name: "shopify_list_products",
    description: "List Shopify products (read-only) including variants, SKU, price and inventory quantity.",
    inputSchema: {
      type: "object",
      properties: {
        limit: {
          type: "integer",
          minimum: 1,
          maximum: 1000,
          default: 50
        },
        query: {
          type: "string",
          description: "Shopify product search query."
        }
      },
      additionalProperties: false
    }
  },
  {
    name: "shopify_customer_purchase_summary",
    description: "Get purchase summary for one customer: total orders, total spent and products/quantities.",
    inputSchema: {
      type: "object",
      properties: {
        customerId: {
          type: "string",
          description: "Shopify customer GraphQL id (gid://shopify/Customer/...)."
        },
        email: {
          type: "string",
          description: "Customer email (used to resolve customer when customerId is missing)."
        },
        limit: {
          type: "integer",
          minimum: 1,
          maximum: 1000,
          default: 250
        }
      },
      additionalProperties: false
    }
  },
  {
    name: "shopify_sales_by_customer_product",
    description:
      "Aggregate purchases across orders to answer who bought what and how much (total spent + quantity by product).",
    inputSchema: {
      type: "object",
      properties: {
        limit: {
          type: "integer",
          minimum: 1,
          maximum: 1000,
          default: 250
        },
        query: {
          type: "string",
          description: "Shopify order search query."
        },
        createdAfter: {
          type: "string",
          format: "date-time"
        },
        createdBefore: {
          type: "string",
          format: "date-time"
        }
      },
      additionalProperties: false
    }
  }
];

export async function callTool(client, name, args = {}) {
  switch (name) {
    case "shopify_list_orders": {
      const orders = await client.listOrders(args);
      return createTextResult({
        count: orders.length,
        orders
      });
    }
    case "shopify_list_customers": {
      const customers = await client.listCustomers(args);
      return createTextResult({
        count: customers.length,
        customers
      });
    }
    case "shopify_list_products": {
      const products = await client.listProducts(args);
      return createTextResult({
        count: products.length,
        products
      });
    }
    case "shopify_customer_purchase_summary": {
      const summary = await client.customerPurchaseSummary(args);
      return createTextResult(summary);
    }
    case "shopify_sales_by_customer_product": {
      const orders = await client.listOrders(args);
      const summary = aggregateByCustomerProduct(orders);
      return createTextResult(summary);
    }
    default:
      throw new Error(`Unknown tool: ${name}`);
  }
}

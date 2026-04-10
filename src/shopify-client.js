import { aggregateByCustomerProduct } from "./analytics.js";

const TOKEN_REFRESH_FALLBACK_SECONDS = 86399;

const ORDERS_QUERY = `
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
`;

const CUSTOMERS_QUERY = `
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
`;

const PRODUCTS_QUERY = `
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
`;

const CUSTOMER_ORDERS_QUERY = `
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
`;

function toNumber(value) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : 0;
}

function toPositiveInt(value, fallbackValue) {
  const parsed = Number.parseInt(String(value), 10);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    return fallbackValue;
  }
  return parsed;
}

async function safeReadJson(response) {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

function errorDetailsFromPayload(payload, fallbackMessage) {
  if (!payload) {
    return fallbackMessage;
  }
  if (payload.errors) {
    return JSON.stringify(payload.errors);
  }
  if (payload.error_description) {
    return payload.error_description;
  }
  if (payload.error) {
    return payload.error;
  }
  return fallbackMessage;
}

function quoteSearchValue(value) {
  if (/^[A-Za-z0-9._:@-]+$/.test(value)) {
    return value;
  }
  return `"${value.replace(/"/g, '\\"')}"`;
}

function buildOrderSearchQuery({ query, createdAfter, createdBefore }) {
  const filters = [];

  if (query?.trim()) {
    filters.push(query.trim());
  }
  if (createdAfter) {
    const iso = new Date(createdAfter).toISOString();
    filters.push(`created_at:>=${iso}`);
  }
  if (createdBefore) {
    const iso = new Date(createdBefore).toISOString();
    filters.push(`created_at:<=${iso}`);
  }

  return filters.join(" ").trim();
}

function mapLineItem(edge) {
  const node = edge.node;
  return {
    productId: node.product?.id ?? null,
    title: node.product?.title ?? node.title,
    sku: node.sku ?? null,
    variantTitle: node.variantTitle ?? null,
    quantity: Number(node.quantity || 0)
  };
}

function mapOrderNode(node) {
  return {
    id: node.id,
    name: node.name,
    createdAt: node.createdAt,
    totalAmount: toNumber(node.totalPriceSet?.shopMoney?.amount),
    currencyCode: node.totalPriceSet?.shopMoney?.currencyCode ?? null,
    customer: node.customer
      ? {
          id: node.customer.id,
          name: node.customer.displayName || null,
          email: node.customer.email || null
        }
      : null,
    items: (node.lineItems?.edges || []).map(mapLineItem)
  };
}

function mapCustomerNode(node) {
  return {
    id: node.id,
    displayName: node.displayName ?? null,
    email: node.email ?? null,
    createdAt: node.createdAt ?? null,
    state: node.state ?? null,
    ordersCount: Number(node.ordersCount || 0),
    amountSpent: toNumber(node.amountSpent?.amount),
    currencyCode: node.amountSpent?.currencyCode ?? null
  };
}

function mapProductNode(node) {
  return {
    id: node.id,
    title: node.title,
    handle: node.handle,
    vendor: node.vendor ?? null,
    productType: node.productType ?? null,
    status: node.status ?? null,
    createdAt: node.createdAt ?? null,
    variants: (node.variants?.edges || []).map((edge) => ({
      id: edge.node.id,
      title: edge.node.title,
      sku: edge.node.sku ?? null,
      price: toNumber(edge.node.price),
      inventoryQuantity: Number(edge.node.inventoryQuantity || 0)
    }))
  };
}

export class ShopifyClient {
  constructor(config, { fetchImpl } = {}) {
    this.config = config;
    this.fetchImpl = fetchImpl || globalThis.fetch;
    if (!this.fetchImpl) {
      throw new Error("No fetch implementation available. Use Node.js 18+.");
    }
    this.endpoint = `https://${config.storeDomain}/admin/api/${config.apiVersion}/graphql.json`;
    this.oauthTokenEndpoint = `https://${config.storeDomain}/admin/oauth/access_token`;
    this.cachedToken = null;
    this.cachedTokenExpiresAt = 0;
  }

  async graphql(query, variables = {}) {
    if (/\bmutation\b/i.test(query)) {
      throw new Error("Read-only mode enabled: GraphQL mutations are blocked.");
    }

    const runGraphql = async () => {
      const accessToken = await this.getAccessToken();
      const response = await this.fetchImpl(this.endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Shopify-Access-Token": accessToken
        },
        body: JSON.stringify({ query, variables })
      });

      const payload = await safeReadJson(response);
      return { response, payload };
    };

    let { response, payload } = await runGraphql();
    if (response.status === 401 && this.config.authMode === "client_credentials") {
      this.invalidateCachedToken();
      ({ response, payload } = await runGraphql());
    }

    if (!response.ok) {
      const details = errorDetailsFromPayload(payload, response.statusText);
      throw new Error(`Shopify API request failed (${response.status}): ${details}`);
    }

    if (payload?.errors?.length) {
      throw new Error(`Shopify GraphQL errors: ${JSON.stringify(payload.errors)}`);
    }

    return payload?.data;
  }

  invalidateCachedToken() {
    this.cachedToken = null;
    this.cachedTokenExpiresAt = 0;
  }

  isCachedTokenStillValid() {
    if (!this.cachedToken || !this.cachedTokenExpiresAt) {
      return false;
    }
    const skewMs = Number(this.config.oauthRefreshSkewSeconds || 60) * 1000;
    return Date.now() < this.cachedTokenExpiresAt - skewMs;
  }

  async getAccessToken() {
    if (this.config.authMode === "static_token") {
      return this.config.staticAccessToken;
    }

    if (this.config.authMode !== "client_credentials") {
      throw new Error(`Unsupported auth mode: ${this.config.authMode}`);
    }

    if (this.isCachedTokenStillValid()) {
      return this.cachedToken;
    }

    return this.exchangeClientCredentialsToken();
  }

  async exchangeClientCredentialsToken() {
    const body = new URLSearchParams({
      grant_type: "client_credentials",
      client_id: this.config.clientId,
      client_secret: this.config.clientSecret
    });

    const response = await this.fetchImpl(this.oauthTokenEndpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        Accept: "application/json"
      },
      body: body.toString()
    });

    const payload = await safeReadJson(response);

    if (!response.ok) {
      const details = errorDetailsFromPayload(payload, response.statusText);
      throw new Error(`Shopify OAuth token request failed (${response.status}): ${details}`);
    }

    if (!payload?.access_token) {
      throw new Error("Shopify OAuth token response missing access_token.");
    }

    const fallbackTtl = toPositiveInt(
      this.config.oauthTokenTtlFallbackSeconds,
      TOKEN_REFRESH_FALLBACK_SECONDS
    );
    const expiresIn = toPositiveInt(payload.expires_in, fallbackTtl);

    this.cachedToken = payload.access_token;
    this.cachedTokenExpiresAt = Date.now() + expiresIn * 1000;

    return this.cachedToken;
  }

  async listOrders({ limit = 50, query, createdAfter, createdBefore } = {}) {
    const cappedLimit = Math.max(1, Math.min(Number(limit || 50), 1000));
    const searchQuery = buildOrderSearchQuery({ query, createdAfter, createdBefore }) || null;
    const orders = [];
    let after = null;
    let hasNextPage = true;

    while (orders.length < cappedLimit && hasNextPage) {
      const first = Math.min(250, cappedLimit - orders.length);
      const data = await this.graphql(ORDERS_QUERY, { first, after, query: searchQuery });
      const edges = data.orders.edges || [];
      for (const edge of edges) {
        orders.push(mapOrderNode(edge.node));
      }
      hasNextPage = data.orders.pageInfo.hasNextPage;
      after = data.orders.pageInfo.endCursor;
    }

    return orders;
  }

  async listCustomers({ limit = 50, query } = {}) {
    const cappedLimit = Math.max(1, Math.min(Number(limit || 50), 1000));
    const customers = [];
    let after = null;
    let hasNextPage = true;

    while (customers.length < cappedLimit && hasNextPage) {
      const first = Math.min(250, cappedLimit - customers.length);
      const data = await this.graphql(CUSTOMERS_QUERY, { first, after, query: query || null });
      const edges = data.customers.edges || [];
      for (const edge of edges) {
        customers.push(mapCustomerNode(edge.node));
      }
      hasNextPage = data.customers.pageInfo.hasNextPage;
      after = data.customers.pageInfo.endCursor;
    }

    return customers;
  }

  async listProducts({ limit = 50, query } = {}) {
    const cappedLimit = Math.max(1, Math.min(Number(limit || 50), 1000));
    const products = [];
    let after = null;
    let hasNextPage = true;

    while (products.length < cappedLimit && hasNextPage) {
      const first = Math.min(250, cappedLimit - products.length);
      const data = await this.graphql(PRODUCTS_QUERY, { first, after, query: query || null });
      const edges = data.products.edges || [];
      for (const edge of edges) {
        products.push(mapProductNode(edge.node));
      }
      hasNextPage = data.products.pageInfo.hasNextPage;
      after = data.products.pageInfo.endCursor;
    }

    return products;
  }

  async resolveCustomerId({ customerId, email }) {
    if (customerId?.trim()) {
      return customerId.trim();
    }

    if (!email?.trim()) {
      throw new Error("Either customerId or email is required.");
    }

    const customers = await this.listCustomers({
      limit: 1,
      query: `email:${quoteSearchValue(email.trim())}`
    });

    if (!customers.length) {
      throw new Error(`No customer found for email: ${email}`);
    }

    return customers[0].id;
  }

  async customerPurchaseSummary({ customerId, email, limit = 250 } = {}) {
    const resolvedCustomerId = await this.resolveCustomerId({ customerId, email });
    const cappedLimit = Math.max(1, Math.min(Number(limit || 250), 1000));
    const orders = [];
    let after = null;
    let hasNextPage = true;
    let customer = null;

    while (orders.length < cappedLimit && hasNextPage) {
      const first = Math.min(250, cappedLimit - orders.length);
      const data = await this.graphql(CUSTOMER_ORDERS_QUERY, {
        id: resolvedCustomerId,
        first,
        after
      });

      if (!data.customer) {
        throw new Error(`Customer not found: ${resolvedCustomerId}`);
      }

      customer = {
        id: data.customer.id,
        name: data.customer.displayName ?? null,
        email: data.customer.email ?? null,
        amountSpent: toNumber(data.customer.amountSpent?.amount),
        currencyCode: data.customer.amountSpent?.currencyCode ?? null
      };

      const edges = data.customer.orders.edges || [];
      for (const edge of edges) {
        const order = mapOrderNode(edge.node);
        order.customer = {
          id: customer.id,
          name: customer.name,
          email: customer.email
        };
        orders.push(order);
      }

      hasNextPage = data.customer.orders.pageInfo.hasNextPage;
      after = data.customer.orders.pageInfo.endCursor;
    }

    const aggregate = aggregateByCustomerProduct(orders);
    const aggregateCustomer = aggregate.customers[0];

    return {
      customer: {
        id: customer?.id ?? resolvedCustomerId,
        name: customer?.name ?? null,
        email: customer?.email ?? null
      },
      totalOrders: aggregateCustomer?.totalOrders ?? 0,
      totalSpent: aggregateCustomer?.totalSpent ?? 0,
      currencyCode: aggregateCustomer?.currencyCode ?? customer?.currencyCode ?? null,
      products: aggregateCustomer?.products ?? []
    };
  }
}

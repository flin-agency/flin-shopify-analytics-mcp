import test from "node:test";
import assert from "node:assert/strict";

import { ShopifyClient } from "../src/shopify-client.js";

const GRAPHQL_URL = "https://my-shop.myshopify.com/admin/api/2025-01/graphql.json";
const TOKEN_URL = "https://my-shop.myshopify.com/admin/oauth/access_token";
const DUMMY_QUERY = "query Ping { shop { name } }";

function makeJsonResponse(status, payload) {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: status === 200 ? "OK" : "ERR",
    async json() {
      return payload;
    }
  };
}

test("static token mode sends GraphQL request without oauth token exchange", async () => {
  const calls = [];
  const fetchImpl = async (url, options) => {
    calls.push({ url, options });
    return makeJsonResponse(200, { data: { shop: { name: "Demo Shop" } } });
  };

  const client = new ShopifyClient(
    {
      storeDomain: "my-shop.myshopify.com",
      apiVersion: "2025-01",
      authMode: "static_token",
      staticAccessToken: "shpat_static"
    },
    { fetchImpl }
  );

  const data = await client.graphql(DUMMY_QUERY, {});
  assert.equal(data.shop.name, "Demo Shop");
  assert.equal(calls.length, 1);
  assert.equal(calls[0].url, GRAPHQL_URL);
  assert.equal(calls[0].options.headers["X-Shopify-Access-Token"], "shpat_static");
});

test("client credentials mode exchanges token once and reuses it while valid", async () => {
  const calls = [];
  const fetchImpl = async (url, options) => {
    calls.push({ url, options });
    if (url === TOKEN_URL) {
      return makeJsonResponse(200, {
        access_token: "dynamic-token-1",
        expires_in: 86400
      });
    }
    return makeJsonResponse(200, { data: { shop: { name: "Demo Shop" } } });
  };

  const client = new ShopifyClient(
    {
      storeDomain: "my-shop.myshopify.com",
      apiVersion: "2025-01",
      authMode: "client_credentials",
      clientId: "cid",
      clientSecret: "csecret",
      oauthRefreshSkewSeconds: 60,
      oauthTokenTtlFallbackSeconds: 86399
    },
    { fetchImpl }
  );

  await client.graphql(DUMMY_QUERY, {});
  await client.graphql(DUMMY_QUERY, {});

  assert.equal(calls.length, 3);
  assert.equal(calls[0].url, TOKEN_URL);
  assert.equal(calls[1].url, GRAPHQL_URL);
  assert.equal(calls[2].url, GRAPHQL_URL);
  assert.equal(calls[1].options.headers["X-Shopify-Access-Token"], "dynamic-token-1");
  assert.equal(calls[2].options.headers["X-Shopify-Access-Token"], "dynamic-token-1");
});

test("client credentials mode refreshes token when cached token is almost expired", async () => {
  const calls = [];
  const tokenPayloads = [
    { access_token: "dynamic-token-1", expires_in: 86400 },
    { access_token: "dynamic-token-2", expires_in: 86400 }
  ];
  const fetchImpl = async (url, options) => {
    calls.push({ url, options });
    if (url === TOKEN_URL) {
      const payload = tokenPayloads.shift();
      return makeJsonResponse(200, payload);
    }
    return makeJsonResponse(200, { data: { shop: { name: "Demo Shop" } } });
  };

  const client = new ShopifyClient(
    {
      storeDomain: "my-shop.myshopify.com",
      apiVersion: "2025-01",
      authMode: "client_credentials",
      clientId: "cid",
      clientSecret: "csecret",
      oauthRefreshSkewSeconds: 60,
      oauthTokenTtlFallbackSeconds: 86399
    },
    { fetchImpl }
  );

  await client.graphql(DUMMY_QUERY, {});
  client.cachedTokenExpiresAt = Date.now() + 500;
  await client.graphql(DUMMY_QUERY, {});

  assert.equal(calls.length, 4);
  assert.equal(calls[0].url, TOKEN_URL);
  assert.equal(calls[1].url, GRAPHQL_URL);
  assert.equal(calls[2].url, TOKEN_URL);
  assert.equal(calls[3].url, GRAPHQL_URL);
  assert.equal(calls[1].options.headers["X-Shopify-Access-Token"], "dynamic-token-1");
  assert.equal(calls[3].options.headers["X-Shopify-Access-Token"], "dynamic-token-2");
});

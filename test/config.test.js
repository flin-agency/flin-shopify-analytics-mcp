import test from "node:test";
import assert from "node:assert/strict";

import { loadConfig, parseCliArgs } from "../src/config.js";

test("loadConfig throws when required env vars are missing", () => {
  assert.throws(() => loadConfig({}), /SHOPIFY_STORE_DOMAIN/);
});

test("loadConfig throws when auth configuration is missing", () => {
  assert.throws(
    () =>
      loadConfig({
        SHOPIFY_STORE_DOMAIN: "my-shop.myshopify.com"
      }),
    /SHOPIFY_ADMIN_ACCESS_TOKEN/
  );
});

test("loadConfig normalizes store domain and loads defaults for static token mode", () => {
  const config = loadConfig({
    SHOPIFY_STORE_DOMAIN: "https://my-shop.myshopify.com/",
    SHOPIFY_ADMIN_ACCESS_TOKEN: "secret-token"
  });

  assert.equal(config.storeDomain, "my-shop.myshopify.com");
  assert.equal(config.authMode, "static_token");
  assert.equal(config.staticAccessToken, "secret-token");
  assert.equal(config.clientId, null);
  assert.equal(config.clientSecret, null);
  assert.equal(config.accessToken, undefined);
  assert.equal(config.oauthRefreshSkewSeconds, 60);
  assert.equal(config.oauthTokenTtlFallbackSeconds, 86399);
  assert.equal(config.apiVersion, "2026-04");
});

test("loadConfig supports client credentials mode", () => {
  const config = loadConfig({
    SHOPIFY_STORE_DOMAIN: "my-shop.myshopify.com",
    SHOPIFY_CLIENT_ID: "client-id",
    SHOPIFY_CLIENT_SECRET: "client-secret",
    SHOPIFY_OAUTH_REFRESH_SKEW_SECONDS: "120",
    SHOPIFY_OAUTH_TOKEN_TTL_FALLBACK_SECONDS: "7200"
  });

  assert.equal(config.authMode, "client_credentials");
  assert.equal(config.staticAccessToken, null);
  assert.equal(config.clientId, "client-id");
  assert.equal(config.clientSecret, "client-secret");
  assert.equal(config.oauthRefreshSkewSeconds, 120);
  assert.equal(config.oauthTokenTtlFallbackSeconds, 7200);
});

test("parseCliArgs maps command line flags", () => {
  const parsed = parseCliArgs([
    "--domain",
    "my-shop.myshopify.com",
    "--clientId",
    "id-1",
    "--clientSecret",
    "sec-1",
    "--apiVersion",
    "2026-01"
  ]);

  assert.deepEqual(parsed, {
    SHOPIFY_STORE_DOMAIN: "my-shop.myshopify.com",
    SHOPIFY_CLIENT_ID: "id-1",
    SHOPIFY_CLIENT_SECRET: "sec-1",
    SHOPIFY_API_VERSION: "2026-01"
  });
});

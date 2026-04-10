const DEFAULT_API_VERSION = "2025-01";
const DEFAULT_OAUTH_REFRESH_SKEW_SECONDS = 60;
const DEFAULT_OAUTH_TOKEN_TTL_FALLBACK_SECONDS = 86399;

function requireEnv(env, name) {
  const value = env[name];
  if (!value || !String(value).trim()) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return String(value).trim();
}

function optionalEnv(env, name) {
  const value = env[name];
  if (value === undefined || value === null) {
    return null;
  }
  const trimmed = String(value).trim();
  return trimmed ? trimmed : null;
}

function normalizeStoreDomain(rawDomain) {
  const withoutProtocol = rawDomain.replace(/^https?:\/\//i, "");
  const withoutPath = withoutProtocol.split("/")[0];
  return withoutPath.replace(/\/+$/, "");
}

function parsePositiveInt(rawValue, fallbackValue, keyName) {
  if (rawValue === undefined || rawValue === null || String(rawValue).trim() === "") {
    return fallbackValue;
  }
  const parsed = Number.parseInt(String(rawValue), 10);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    throw new Error(`${keyName} must be a positive integer.`);
  }
  return parsed;
}

export function parseCliArgs(argv = process.argv.slice(2)) {
  const output = {};

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (!arg.startsWith("--")) {
      continue;
    }

    const value = argv[i + 1];
    if (value === undefined || value.startsWith("--")) {
      throw new Error(`Missing value for argument: ${arg}`);
    }

    i += 1;

    switch (arg) {
      case "--domain":
      case "--storeDomain":
        output.SHOPIFY_STORE_DOMAIN = value;
        break;
      case "--accessToken":
      case "--adminAccessToken":
        output.SHOPIFY_ADMIN_ACCESS_TOKEN = value;
        break;
      case "--clientId":
        output.SHOPIFY_CLIENT_ID = value;
        break;
      case "--clientSecret":
        output.SHOPIFY_CLIENT_SECRET = value;
        break;
      case "--apiVersion":
        output.SHOPIFY_API_VERSION = value;
        break;
      case "--oauthRefreshSkewSeconds":
        output.SHOPIFY_OAUTH_REFRESH_SKEW_SECONDS = value;
        break;
      case "--oauthTokenTtlFallbackSeconds":
        output.SHOPIFY_OAUTH_TOKEN_TTL_FALLBACK_SECONDS = value;
        break;
      default:
        throw new Error(`Unknown argument: ${arg}`);
    }
  }

  return output;
}

export function loadConfig(env = process.env, overrides = {}) {
  const merged = { ...env, ...overrides };
  const storeDomain = normalizeStoreDomain(requireEnv(merged, "SHOPIFY_STORE_DOMAIN"));
  const apiVersion = (merged.SHOPIFY_API_VERSION || DEFAULT_API_VERSION).trim();

  if (!storeDomain) {
    throw new Error("SHOPIFY_STORE_DOMAIN is invalid.");
  }

  const staticAccessToken = optionalEnv(merged, "SHOPIFY_ADMIN_ACCESS_TOKEN");
  const clientId = optionalEnv(merged, "SHOPIFY_CLIENT_ID");
  const clientSecret = optionalEnv(merged, "SHOPIFY_CLIENT_SECRET");
  const oauthRefreshSkewSeconds = parsePositiveInt(
    merged.SHOPIFY_OAUTH_REFRESH_SKEW_SECONDS,
    DEFAULT_OAUTH_REFRESH_SKEW_SECONDS,
    "SHOPIFY_OAUTH_REFRESH_SKEW_SECONDS"
  );
  const oauthTokenTtlFallbackSeconds = parsePositiveInt(
    merged.SHOPIFY_OAUTH_TOKEN_TTL_FALLBACK_SECONDS,
    DEFAULT_OAUTH_TOKEN_TTL_FALLBACK_SECONDS,
    "SHOPIFY_OAUTH_TOKEN_TTL_FALLBACK_SECONDS"
  );

  let authMode = null;
  if (staticAccessToken) {
    authMode = "static_token";
  } else if (clientId || clientSecret) {
    if (!clientId || !clientSecret) {
      throw new Error(
        "Both SHOPIFY_CLIENT_ID and SHOPIFY_CLIENT_SECRET are required for client credentials mode."
      );
    }
    authMode = "client_credentials";
  }

  if (!authMode) {
    throw new Error(
      "Missing auth configuration. Set SHOPIFY_ADMIN_ACCESS_TOKEN or SHOPIFY_CLIENT_ID + SHOPIFY_CLIENT_SECRET."
    );
  }

  return {
    storeDomain,
    apiVersion,
    authMode,
    staticAccessToken: staticAccessToken || null,
    clientId: clientId || null,
    clientSecret: clientSecret || null,
    oauthRefreshSkewSeconds,
    oauthTokenTtlFallbackSeconds
  };
}

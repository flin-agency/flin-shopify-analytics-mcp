import { loadConfig } from "./config.js";
import { ShopifyClient } from "./shopify-client.js";
import { TOOL_DEFINITIONS, callTool } from "./tools.js";

const JSONRPC_VERSION = "2.0";
const DEFAULT_PROTOCOL_VERSION = "2025-03-26";
const SERVER_INFO = {
  name: "flin-shopify-analytics-mcp",
  version: "0.1.0"
};

function isNotification(message) {
  return message.id === undefined;
}

function makeError(code, message, data) {
  const error = { code, message };
  if (data !== undefined) {
    error.data = data;
  }
  return error;
}

export class ShopifyAnalyticsMcpServer {
  constructor({ client, config, fetchImpl } = {}) {
    this.client = client;
    if (!this.client) {
      const resolvedConfig = config || loadConfig();
      this.client = new ShopifyClient(resolvedConfig, { fetchImpl });
    }
    this.initialized = false;
  }

  async handleMessage(message) {
    if (!message || typeof message !== "object") {
      return {
        jsonrpc: JSONRPC_VERSION,
        id: null,
        error: makeError(-32600, "Invalid Request")
      };
    }

    if (typeof message.method !== "string") {
      if (isNotification(message)) {
        return null;
      }
      return {
        jsonrpc: JSONRPC_VERSION,
        id: message.id ?? null,
        error: makeError(-32600, "Invalid Request")
      };
    }

    try {
      const result = await this.dispatch(message.method, message.params ?? {});
      if (isNotification(message)) {
        return null;
      }
      return {
        jsonrpc: JSONRPC_VERSION,
        id: message.id,
        result
      };
    } catch (error) {
      if (isNotification(message)) {
        return null;
      }
      const code = Number.isInteger(error.code) ? error.code : -32000;
      return {
        jsonrpc: JSONRPC_VERSION,
        id: message.id ?? null,
        error: makeError(code, error.message || "Internal error")
      };
    }
  }

  async dispatch(method, params) {
    switch (method) {
      case "initialize":
        this.initialized = true;
        return {
          protocolVersion: params.protocolVersion || DEFAULT_PROTOCOL_VERSION,
          capabilities: {
            tools: {}
          },
          serverInfo: SERVER_INFO
        };
      case "notifications/initialized":
        return {};
      case "ping":
        return {};
      case "tools/list":
        this.assertInitialized(method);
        return { tools: TOOL_DEFINITIONS };
      case "tools/call":
        this.assertInitialized(method);
        return this.handleToolCall(params);
      case "resources/list":
        this.assertInitialized(method);
        return { resources: [] };
      case "prompts/list":
        this.assertInitialized(method);
        return { prompts: [] };
      default:
        throw { code: -32601, message: `Method not found: ${method}` };
    }
  }

  assertInitialized(method) {
    if (!this.initialized) {
      throw { code: -32002, message: `Server not initialized. Call initialize before ${method}.` };
    }
  }

  async handleToolCall(params) {
    const name = params?.name;
    if (!name || typeof name !== "string") {
      throw { code: -32602, message: "Invalid params: tools/call requires a string `name`." };
    }

    try {
      return await callTool(this.client, name, params.arguments || {});
    } catch (error) {
      return {
        content: [{ type: "text", text: `Tool failed: ${error.message}` }],
        isError: true
      };
    }
  }
}

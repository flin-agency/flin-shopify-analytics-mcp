#!/usr/bin/env node

import { loadConfig, parseCliArgs } from "./config.js";
import { ShopifyAnalyticsMcpServer } from "./mcp-server.js";

let server;
try {
  const cliOverrides = parseCliArgs(process.argv.slice(2));
  const config = loadConfig(process.env, cliOverrides);
  server = new ShopifyAnalyticsMcpServer({ config });
} catch (error) {
  process.stderr.write(`[startup] ${error.message}\n`);
  process.exit(1);
}

let buffer = Buffer.alloc(0);
let processing = Promise.resolve();

process.stdin.on("data", (chunk) => {
  buffer = Buffer.concat([buffer, chunk]);
  readFrames();
});

process.stdin.on("end", () => {
  process.exit(0);
});

process.stdin.resume();

function readFrames() {
  while (true) {
    const headerEnd = buffer.indexOf("\r\n\r\n");
    if (headerEnd === -1) {
      return;
    }

    const header = buffer.slice(0, headerEnd).toString("utf8");
    const lengthMatch = header.match(/Content-Length:\s*(\d+)/i);
    if (!lengthMatch) {
      buffer = buffer.slice(headerEnd + 4);
      continue;
    }

    const contentLength = Number(lengthMatch[1]);
    const frameStart = headerEnd + 4;
    const frameEnd = frameStart + contentLength;
    if (buffer.length < frameEnd) {
      return;
    }

    const payloadRaw = buffer.slice(frameStart, frameEnd).toString("utf8");
    buffer = buffer.slice(frameEnd);

    queueMessage(payloadRaw);
  }
}

function queueMessage(payloadRaw) {
  processing = processing
    .then(async () => {
      const message = JSON.parse(payloadRaw);
      const response = await server.handleMessage(message);
      if (response) {
        writeFrame(response);
      }
    })
    .catch((error) => {
      const response = {
        jsonrpc: "2.0",
        id: null,
        error: {
          code: -32700,
          message: `Parse error: ${error.message}`
        }
      };
      writeFrame(response);
    });
}

function writeFrame(payload) {
  const body = JSON.stringify(payload);
  const header = `Content-Length: ${Buffer.byteLength(body, "utf8")}\r\n\r\n`;
  process.stdout.write(header + body);
}

"""CLI entrypoint for stdio MCP server."""

from __future__ import annotations

import json
import sys
from typing import Any

from .config import load_config, parse_cli_args
from .mcp_server import ShopifyAnalyticsMcpServer


def _find_header_end(buffer: bytes) -> tuple[int, int]:
    crlf_pos = buffer.find(b"\r\n\r\n")
    lf_pos = buffer.find(b"\n\n")

    candidates: list[tuple[int, int]] = []
    if crlf_pos >= 0:
        candidates.append((crlf_pos, 4))
    if lf_pos >= 0:
        candidates.append((lf_pos, 2))

    if not candidates:
        return -1, 0
    return min(candidates, key=lambda item: item[0])


def _read_frames(stdin: Any):
    buffer = b""
    while True:
        chunk = stdin.buffer.read1(4096)
        if not chunk:
            break
        buffer += chunk
        while True:
            header_end, separator_len = _find_header_end(buffer)
            if header_end < 0:
                break
            header = buffer[:header_end].decode("utf-8", errors="replace")
            content_length = None
            for line in header.replace("\r\n", "\n").split("\n"):
                if line.lower().startswith("content-length:"):
                    content_length = int(line.split(":", 1)[1].strip())
                    break
            if content_length is None:
                buffer = buffer[header_end + separator_len :]
                continue
            frame_start = header_end + separator_len
            frame_end = frame_start + content_length
            if len(buffer) < frame_end:
                break
            payload = buffer[frame_start:frame_end]
            buffer = buffer[frame_end:]
            yield payload


def _write_frame(stdout: Any, payload: dict[str, Any]) -> None:
    body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8")
    stdout.buffer.write(header + body)
    stdout.flush()


def main(argv: list[str] | None = None) -> int:
    try:
        cli_overrides = parse_cli_args(argv or sys.argv[1:])
        config = load_config(overrides=cli_overrides)
    except Exception as exc:
        sys.stderr.write(f"[startup] {exc}\n")
        return 1

    server = ShopifyAnalyticsMcpServer(config=config)
    for payload_raw in _read_frames(sys.stdin):
        try:
            message = json.loads(payload_raw.decode("utf-8"))
            response = server.handle_message(message)
        except Exception as exc:
            response = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(exc)}}
        if response is not None:
            _write_frame(sys.stdout, response)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

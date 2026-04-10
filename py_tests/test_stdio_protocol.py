from __future__ import annotations

import os
import subprocess
import sys
import unittest


INIT_PAYLOAD = b'{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'


def _run_server_with_input(raw_input: bytes) -> tuple[bytes, bytes, int]:
    env = os.environ.copy()
    env.update(
        {
            "SHOPIFY_STORE_DOMAIN": "my-shop.myshopify.com",
            "SHOPIFY_CLIENT_ID": "dummy-client",
            "SHOPIFY_CLIENT_SECRET": "dummy-secret",
            "PYTHONPATH": ".",
        }
    )
    proc = subprocess.Popen(
        [sys.executable, "-m", "flin_shopify_analytics_mcp"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        cwd=os.getcwd(),
    )
    out, err = proc.communicate(raw_input, timeout=5)
    return out, err, proc.returncode


class StdioProtocolTests(unittest.TestCase):
    def test_handles_crlf_headers(self) -> None:
        raw_input = b"Content-Length: " + str(len(INIT_PAYLOAD)).encode("ascii") + b"\r\n\r\n" + INIT_PAYLOAD
        out, err, code = _run_server_with_input(raw_input)
        self.assertEqual(code, 0)
        self.assertEqual(err, b"")
        self.assertIn(b'"result"', out)

    def test_handles_lf_only_headers(self) -> None:
        raw_input = b"Content-Length: " + str(len(INIT_PAYLOAD)).encode("ascii") + b"\n\n" + INIT_PAYLOAD
        out, err, code = _run_server_with_input(raw_input)
        self.assertEqual(code, 0)
        self.assertEqual(err, b"")
        self.assertIn(b'"result"', out)


if __name__ == "__main__":
    unittest.main()

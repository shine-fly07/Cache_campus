import io
import json
import unittest

from src.cache_sim.ui import CacheSession, make_handler


class _MockSocket:
    def __init__(self, raw_request: bytes):
        self._rfile = io.BytesIO(raw_request)
        self.wfile = io.BytesIO()

    def makefile(self, mode, *args, **kwargs):
        if "r" in mode:
            return self._rfile
        return self.wfile

    def sendall(self, data):
        self.wfile.write(data)


def _dispatch_http(handler_cls, method, path, body=None):
    payload = b"" if body is None else json.dumps(body).encode("utf-8")
    headers = (
        f"{method} {path} HTTP/1.1\r\n"
        f"Host: 127.0.0.1\r\n"
        f"Content-Length: {len(payload)}\r\n"
        f"Content-Type: application/json\r\n\r\n"
    ).encode("ascii")
    sock = _MockSocket(headers + payload)
    handler_cls(sock, ("127.0.0.1", 12345), None)
    raw = sock.wfile.getvalue()
    head, resp_body = raw.split(b"\r\n\r\n", 1)
    status_line = head.split(b"\r\n", 1)[0].decode("ascii")
    status_code = int(status_line.split()[1])
    return status_code, resp_body


class TestCacheSession(unittest.TestCase):
    def test_put_get_evict_and_analytics_snapshot(self):
        session = CacheSession(initial_capacity=2)
        session.execute_line("PUT A 10")
        session.execute_line("PUT B 20")
        session.execute_line("GET A")
        res = session.execute_line("PUT C 30")

        snap = res["snapshot"]
        self.assertEqual(snap["capacity"], 2)
        self.assertEqual(snap["size"], 2)
        self.assertEqual(snap["min_freq"], 1)
        self.assertEqual(snap["state"], [{"key": "C", "freq": 1}, {"key": "A", "freq": 2}])

        self.assertEqual(snap["analytics"]["hits"], 1)
        self.assertEqual(snap["analytics"]["misses"], 0)
        self.assertEqual(snap["analytics"]["evictions"], 1)
        self.assertEqual(snap["analytics"]["evictions_by_freq"], [{"freq": 1, "count": 1}])
        self.assertEqual(snap["last_event"]["evicted"]["key"], "B")

        self.assertEqual(snap["hashmap_stats"]["key_map"]["size"], 2)
        self.assertEqual(snap["hashmap_stats"]["freq_map"]["size"], 2)

    def test_run_script_and_comments_skipped(self):
        session = CacheSession(initial_capacity=3)
        snap = session.run_script(
            "# comment\n\nCAPACITY 2\nPUT X 1\nGET MISSING\nANALYTICS\n"
        )
        self.assertEqual(snap["step_count"], 4)
        self.assertEqual(snap["analytics"]["misses"], 1)
        self.assertIn("ANALYTICS ->", snap["logs"][-1])

    def test_unimplemented_resize_raises_value_error(self):
        session = CacheSession(initial_capacity=2)
        with self.assertRaises(ValueError):
            session.execute_line("RESIZE 4")


class TestWebUIHTTP(unittest.TestCase):
    def test_http_endpoints(self):
        session = CacheSession(initial_capacity=2)
        handler_cls = make_handler(session)

        status, body = _dispatch_http(handler_cls, "GET", "/")
        self.assertEqual(status, 200)
        self.assertIn("CampusCache", body.decode("utf-8"))

        status, body = _dispatch_http(handler_cls, "GET", "/api/demo")
        self.assertEqual(status, 200)
        self.assertIn("CAPACITY", json.loads(body)["script"])

        status, body = _dispatch_http(handler_cls, "POST", "/api/exec", {"line": "PUT A 10"})
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["snapshot"]["size"], 1)

        status, body = _dispatch_http(handler_cls, "POST", "/api/exec", {"line": "BOGUS"})
        self.assertEqual(status, 400)
        self.assertIn("error", json.loads(body))

        status, body = _dispatch_http(handler_cls, "POST", "/api/reset", {"capacity": 3})
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["capacity"], 3)
        self.assertEqual(json.loads(body)["size"], 0)

        status, _ = _dispatch_http(handler_cls, "GET", "/api/unknown")
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()

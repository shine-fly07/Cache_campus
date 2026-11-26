"""Interactive Web UI server and session manager for CampusCache LFU Simulator."""

import argparse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
import webbrowser

from .analytics import Analytics
from .cache import LFUCache
from .simulator import MAX_OPERATIONS, parse_line


STATIC_DIR = Path(__file__).resolve().parent / "static"
DEMO_PATH = Path(__file__).resolve().parents[2] / "demo" / "sequence.txt"


def _insertion_sort_ints(values):
    arr = list(values)
    for i in range(1, len(arr)):
        cur = arr[i]
        j = i - 1
        while j >= 0 and arr[j] > cur:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = cur
    return arr


def _hashmap_metrics(hm):
    buckets = getattr(hm, "_buckets", [])
    bucket_count = hm.bucket_count() if hasattr(hm, "bucket_count") else len(buckets)
    non_empty = 0
    max_chain = 0
    for chain in buckets:
        if chain:
            non_empty += 1
            if len(chain) > max_chain:
                max_chain = len(chain)
    return {
        "size": len(hm),
        "bucket_count": bucket_count,
        "load_factor": round(hm.load_factor(), 4) if hasattr(hm, "load_factor") else 0.0,
        "non_empty_buckets": non_empty,
        "max_chain_length": max_chain,
    }


def _normalize_evicted(evicted):
    if not evicted:
        return None
    if isinstance(evicted, dict):
        return {
            "key": evicted.get("key"),
            "freq": evicted.get("freq"),
            "reason": evicted.get("reason", "LFU"),
        }
    if isinstance(evicted, tuple) and len(evicted) >= 2:
        reason = evicted[2] if len(evicted) >= 3 else "LFU"
        return {"key": evicted[0], "freq": evicted[1], "reason": reason}
    return {"key": str(evicted), "freq": None, "reason": "evicted"}


class CacheSession:
    """Thread-safe stateful wrapper around LFUCache + Analytics for the Web UI."""

    def __init__(self, initial_capacity=3):
        self._lock = threading.Lock()
        self.cache = None
        self.analytics = None
        self.logs = []
        self.step_count = 0
        self.last_event = None
        self.reset(initial_capacity)

    def reset(self, capacity=3):
        with self._lock:
            self.cache = LFUCache(capacity)
            self.analytics = Analytics()
            self.logs = []
            self.step_count = 0
            self.last_event = {
                "type": "CAPACITY",
                "detail": f"Initialized cache with capacity {capacity}",
                "evicted": None,
            }
            return self._snapshot_unlocked()

    def execute_line(self, raw_line):
        with self._lock:
            parsed = parse_line(raw_line)
            if parsed is None:
                return {"skipped": True, "snapshot": self._snapshot_unlocked()}

            if self.step_count >= MAX_OPERATIONS:
                raise ValueError(f"Operation limit of {MAX_OPERATIONS} exceeded")

            self.step_count += 1
            prefix = f"[{self.step_count:02d}]"
            cmd = parsed[0]

            if cmd == "CAPACITY":
                cap = parsed[1]
                self.cache = LFUCache(cap)
                self.analytics = Analytics()
                msg = f"{prefix} CAPACITY {cap} -> OK"
                self.logs.append(msg)
                self.last_event = {
                    "type": "CAPACITY",
                    "detail": f"Cache reset with capacity {cap}",
                    "evicted": None,
                }

            elif cmd == "PUT":
                _, key, value = parsed
                was_present = self.cache.key_map.contains(key)
                res = self.cache.put(key, value)
                action = res.get("action", "inserted")
                evicted_info = _normalize_evicted(res.get("evicted"))

                if action == "inserted":
                    self.analytics.record_insert(key)
                elif action == "updated" and was_present:
                    self.analytics.record_hit(key)

                if evicted_info is not None and evicted_info["freq"] is not None:
                    self.analytics.record_eviction(evicted_info["key"], evicted_info["freq"])

                msg = f"{prefix} PUT {key}={value} -> {action}"
                if evicted_info is not None:
                    msg += (
                        f" | EVICTED {evicted_info['key']} "
                        f"(freq {evicted_info['freq']}, {evicted_info['reason']})"
                    )
                self.logs.append(msg)
                self.last_event = {
                    "type": "PUT",
                    "action": action,
                    "key": key,
                    "value": value,
                    "detail": msg,
                    "evicted": evicted_info,
                }

            elif cmd == "GET":
                _, key = parsed
                hit, val, old_freq, new_freq = self.cache.get(key)
                if hit:
                    self.analytics.record_hit(key)
                    msg = f"{prefix} GET {key} -> HIT {val} (freq {old_freq}->{new_freq})"
                    self.last_event = {
                        "type": "GET",
                        "hit": True,
                        "key": key,
                        "value": val,
                        "old_freq": old_freq,
                        "new_freq": new_freq,
                        "detail": msg,
                        "evicted": None,
                    }
                else:
                    self.analytics.record_miss()
                    msg = f"{prefix} GET {key} -> MISS"
                    self.last_event = {
                        "type": "GET",
                        "hit": False,
                        "key": key,
                        "detail": msg,
                        "evicted": None,
                    }
                self.logs.append(msg)

            elif cmd == "STATE":
                current = self.cache.state()
                msg = f"{prefix} STATE -> {current}"
                self.logs.append(msg)
                self.last_event = {
                    "type": "STATE",
                    "detail": msg,
                    "evicted": None,
                }

            elif cmd == "RESIZE":
                new_cap = parsed[1]
                try:
                    self.cache.resize(new_cap)
                except NotImplementedError as exc:
                    self.step_count -= 1
                    raise ValueError("RESIZE is not yet implemented in LFUCache") from exc
                msg = f"{prefix} RESIZE {new_cap} -> OK"
                self.logs.append(msg)
                self.last_event = {
                    "type": "RESIZE",
                    "detail": msg,
                    "evicted": None,
                }

            elif cmd == "ANALYTICS":
                summary = self.analytics.report().replace("\n", " | ")
                msg = f"{prefix} ANALYTICS -> {summary}"
                self.logs.append(msg)
                self.last_event = {
                    "type": "ANALYTICS",
                    "detail": msg,
                    "evicted": None,
                }

            return {"skipped": False, "snapshot": self._snapshot_unlocked()}

    def run_script(self, script_text):
        for line in script_text.splitlines():
            self.execute_line(line)
        return self.snapshot()

    def snapshot(self):
        with self._lock:
            return self._snapshot_unlocked()

    def _snapshot_unlocked(self):
        freqs = _insertion_sort_ints(self.cache.freq_map.keys())
        freq_buckets = []
        for freq in freqs:
            dll = self.cache.freq_map.get(freq)
            nodes = []
            # reversed(dll) iterates LRU -> MRU so the left-most card is the eviction victim.
            for node in reversed(dll):
                nodes.append({
                    "key": node.key,
                    "value": node.value,
                    "freq": node.freq,
                })
            freq_buckets.append({
                "freq": freq,
                "is_min_freq": freq == self.cache.min_freq and self.cache.size > 0,
                "nodes": nodes,
            })

        state_list = [{"key": k, "freq": f} for k, f in self.cache.state()]
        ev_freqs = [
            {"freq": f, "count": c}
            for f, c in self.analytics._sorted_freq_items()
        ]
        total_lookups = self.analytics.hits + self.analytics.misses

        return {
            "capacity": self.cache.capacity,
            "size": self.cache.size,
            "min_freq": self.cache.min_freq,
            "step_count": self.step_count,
            "state": state_list,
            "freq_buckets": freq_buckets,
            "hashmap_stats": {
                "key_map": _hashmap_metrics(self.cache.key_map),
                "freq_map": _hashmap_metrics(self.cache.freq_map),
            },
            "analytics": {
                "hits": self.analytics.hits,
                "misses": self.analytics.misses,
                "lookups": total_lookups,
                "hit_ratio": round(self.analytics.hit_ratio() * 100.0, 1),
                "evictions": self.analytics.evictions,
                "evictions_by_freq": ev_freqs,
                "longest_lived_key": self.analytics.longest_lived_key,
                "last_evicted": self.analytics.last_evicted,
                "report": self.analytics.report(),
            },
            "logs": list(self.logs),
            "last_event": self.last_event,
        }


def load_demo_script():
    if DEMO_PATH.exists():
        return DEMO_PATH.read_text(encoding="utf-8")
    return "CAPACITY 3\nPUT A 10\nPUT B 20\nGET A\nPUT C 30\nSTATE\n"


def make_handler(session):
    """Build an HTTP request handler bound to a CacheSession instance."""

    class CacheUIHandler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            # Keep server stdout clean during CLI/test execution.
            return

        def _send_json(self, status, payload):
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _read_json_body(self):
            length = int(self.headers.get("Content-Length", "0") or 0)
            if length == 0:
                return {}
            raw = self.rfile.read(length)
            return json.loads(raw.decode("utf-8"))

        def do_GET(self):
            path = self.path.split("?", 1)[0]
            if path in ("/", "/index.html"):
                html_path = STATIC_DIR / "index.html"
                content = html_path.read_bytes()
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return

            if path == "/api/state":
                self._send_json(HTTPStatus.OK, session.snapshot())
                return

            if path == "/api/demo":
                self._send_json(HTTPStatus.OK, {"script": load_demo_script()})
                return

            self._send_json(HTTPStatus.NOT_FOUND, {"error": f"Unknown endpoint: {path}"})

        def do_POST(self):
            path = self.path.split("?", 1)[0]
            try:
                body = self._read_json_body()
                if path == "/api/reset":
                    capacity = int(body.get("capacity", 3))
                    snap = session.reset(capacity)
                    self._send_json(HTTPStatus.OK, snap)
                    return

                if path == "/api/exec":
                    line = body.get("line", "")
                    result = session.execute_line(line)
                    self._send_json(HTTPStatus.OK, result)
                    return

                if path == "/api/run":
                    script = body.get("script", "")
                    if body.get("reset", True):
                        session.reset(int(body.get("capacity", session.cache.capacity)))
                    snap = session.run_script(script)
                    self._send_json(HTTPStatus.OK, snap)
                    return

                self._send_json(HTTPStatus.NOT_FOUND, {"error": f"Unknown endpoint: {path}"})
            except (ValueError, TypeError, json.JSONDecodeError) as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    return CacheUIHandler


def create_server(host="127.0.0.1", port=8000, initial_capacity=3):
    session = CacheSession(initial_capacity=initial_capacity)
    server = ThreadingHTTPServer((host, port), make_handler(session))
    return server, session


def main(argv=None):
    parser = argparse.ArgumentParser(description="Launch the CampusCache Web UI")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    parser.add_argument("--capacity", type=int, default=3, help="Initial cache capacity (0-200)")
    parser.add_argument("--no-browser", action="store_true", help="Do not open browser automatically")
    args = parser.parse_args(argv)

    server, _ = create_server(host=args.host, port=args.port, initial_capacity=args.capacity)
    url = f"http://{args.host}:{server.server_address[1]}/"
    print(f"CampusCache Web UI running at {url} (Ctrl+C to stop)")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down CampusCache Web UI.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

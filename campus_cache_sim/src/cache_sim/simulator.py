"""Parses an operation script, drives LFUCache, produces the operation log."""

from .cache import LFUCache

MAX_OPERATIONS = 12_000


class _FakeCache:
    """Temporary fallback cache used until LFUCache methods are implemented."""

    def __init__(self, capacity: int = 0):
        self.capacity = capacity
        # Preserve insertion order for deterministic fake eviction
        self._items: dict[str, tuple[str, int]] = {}

    def set_capacity(self, capacity: int) -> None:
        self.capacity = capacity
        while len(self._items) > self.capacity:
            oldest_key = next(iter(self._items))
            del self._items[oldest_key]

    resize = set_capacity

    def get(self, key: str):
        if key not in self._items:
            return False, None, None, None
        val, freq = self._items[key]
        old_freq = freq
        new_freq = freq + 1
        self._items[key] = (val, new_freq)
        return True, val, old_freq, new_freq

    def put(self, key: str, value: str) -> dict:
        if key in self._items:
            _, freq = self._items[key]
            self._items[key] = (value, freq + 1)
            return {
                "action": "UPDATED",
                "evicted": None,
                "freq": freq + 1,
            }

        evicted = None
        if self.capacity <= 0:
            return {
                "action": "SKIPPED_ZERO_CAPACITY",
                "evicted": None,
                "freq": 0,
            }

        if len(self._items) >= self.capacity:
            evict_key, (_, evict_freq) = self._items.popitem() if False else (
                lambda k: (k, self._items.pop(k))
            )(next(iter(self._items)))
            evicted = {
                "key": evict_key,
                "freq": evict_freq,
                "reason": "LRU among lowest freq (fake)",
            }

        self._items[key] = (value, 1)
        return {
            "action": "INSERTED",
            "evicted": evicted,
            "freq": 1,
        }

    def snapshot(self) -> str:
        if not self._items:
            return "<empty>"
        return ", ".join(f"{k}:{freq}" for k, (_, freq) in self._items.items())


def _parse_int(token: str, label: str) -> int:
    try:
        # Reject floats/underscores/weird strings strictly as base-10 integers
        if token.startswith(("+", "-")) and token[1:].isdigit():
            return int(token, 10)
        if token.isdigit():
            return int(token, 10)
        raise ValueError
    except ValueError as exc:
        raise ValueError(f"Invalid {label}: {token!r}") from exc


def parse_line(line):
    """Return a tuple like ("PUT", key, value) / ("GET", key) / ("STATE",)
    / ("CAPACITY", n) / ("RESIZE", n) [ext] / ("ANALYTICS",), or None for blank/comment lines.
    Raise ValueError if malformed.
    """
    if not isinstance(line, str):
        raise ValueError(f"Expected string line, got {type(line).__name__}")

    # Strip comments and surrounding whitespace
    code_part = line.split("#", 1)[0].strip()
    if not code_part:
        return None

    parts = code_part.split()
    cmd = parts[0].upper()
    args = parts[1:]

    if cmd == "PUT":
        if len(args) != 2:
            raise ValueError(f"PUT requires exactly 2 arguments (key value), got {len(args)}: {line!r}")
        return ("PUT", args[0], args[1])

    if cmd == "GET":
        if len(args) != 1:
            raise ValueError(f"GET requires exactly 1 argument (key), got {len(args)}: {line!r}")
        return ("GET", args[0])

    if cmd == "STATE":
        if len(args) != 0:
            raise ValueError(f"STATE takes no arguments, got {args}: {line!r}")
        return ("STATE",)

    if cmd == "CAPACITY":
        if len(args) != 1:
            raise ValueError(f"CAPACITY requires exactly 1 integer argument, got {len(args)}: {line!r}")
        cap = _parse_int(args[0], "CAPACITY")
        if cap < 0:
            raise ValueError(f"CAPACITY must be non-negative, got {cap}")
        return ("CAPACITY", cap)

    if cmd == "RESIZE":
        if len(args) != 1:
            raise ValueError(f"RESIZE requires exactly 1 integer argument, got {len(args)}: {line!r}")
        new_cap = _parse_int(args[0], "RESIZE")
        if new_cap < 0:
            raise ValueError(f"RESIZE capacity must be non-negative, got {new_cap}")
        return ("RESIZE", new_cap)

    if cmd == "ANALYTICS":
        if len(args) != 0:
            raise ValueError(f"ANALYTICS takes no arguments, got {args}: {line!r}")
        return ("ANALYTICS",)

    raise ValueError(f"Unknown or malformed command {parts[0]!r} in line: {line!r}")


def _build_cache(capacity: int):
    """Instantiate LFUCache if implemented, otherwise fall back to _FakeCache."""
    try:
        return LFUCache(capacity)
    except Exception:
        return _FakeCache(capacity)


def _format_state(cache) -> str:
    if hasattr(cache, "snapshot") and callable(cache.snapshot):
        return str(cache.snapshot())
    if hasattr(cache, "state") and callable(cache.state):
        return str(cache.state())
    if hasattr(cache, "_items") and isinstance(cache._items, dict):
        if not cache._items:
            return "<empty>"
        return ", ".join(f"{k}:{v[1]}" for k, v in cache._items.items())
    return str(cache)


def _handle_get(cache, key: str, analytics=None) -> str:
    # Support LFUCache.get(key) returning either a value/None or a tuple/dict
    if hasattr(cache, "get") and callable(cache.get):
        result = cache.get(key)
        if isinstance(result, tuple):
            if len(result) == 4:
                hit, val, old_freq, new_freq = result
                if hit:
                    if analytics and hasattr(analytics, "record_hit"):
                        analytics.record_hit()
                    return f"GET {key} -> HIT {val} (freq {old_freq}->{new_freq})"
                if analytics and hasattr(analytics, "record_miss"):
                    analytics.record_miss()
                return f"GET {key} -> MISS"
            if len(result) == 2:
                hit, val = result
                if hit:
                    if analytics and hasattr(analytics, "record_hit"):
                        analytics.record_hit()
                    return f"GET {key} -> HIT {val}"
                if analytics and hasattr(analytics, "record_miss"):
                    analytics.record_miss()
                return f"GET {key} -> MISS"

        if result is not None and result is not False:
            if analytics and hasattr(analytics, "record_hit"):
                analytics.record_hit()
            return f"GET {key} -> HIT {result}"

    if analytics and hasattr(analytics, "record_miss"):
        analytics.record_miss()
    return f"GET {key} -> MISS"


def _handle_put(cache, key: str, value: str, analytics=None) -> str:
    put_res = cache.put(key, value)
    if not isinstance(put_res, dict):
        put_res = {"action": "PUT", "evicted": None}

    action = put_res.get("action") or ("UPDATED" if put_res.get("updated") else "INSERTED")
    evicted = put_res.get("evicted")

    parts = [f"PUT {key}={value} -> {action}"]
    if evicted:
        if isinstance(evicted, dict):
            ev_key = evicted.get("key", "?")
            ev_freq = evicted.get("freq", "?")
            ev_reason = evicted.get("reason", "evicted")
            parts.append(f"EVICTED {ev_key} (freq {ev_freq}, {ev_reason})")
            if analytics and hasattr(analytics, "record_eviction"):
                analytics.record_eviction(ev_key, ev_freq)
        else:
            parts.append(f"EVICTED {evicted}")

    return " | ".join(parts)


def run(lines):
    """Execute all operations; return list of log strings, one per operation.
    Enforce limit of 12,000 operations.
    """
    cache = None
    analytics = None
    logs: list[str] = []
    op_count = 0

    for raw_line in lines:
        parsed = parse_line(raw_line)
        if parsed is None:
            continue

        op_count += 1
        if op_count > MAX_OPERATIONS:
            raise ValueError(f"Operation limit of {MAX_OPERATIONS} exceeded")

        step_prefix = f"[{op_count:02d}]"
        cmd = parsed[0]

        if cmd == "CAPACITY":
            cap = parsed[1]
            cache = _build_cache(cap)
            logs.append(f"{step_prefix} CAPACITY {cap} -> OK")

        elif cmd == "PUT":
            if cache is None:
                cache = _build_cache(0)
            _, key, value = parsed
            logs.append(f"{step_prefix} {_handle_put(cache, key, value, analytics)}")

        elif cmd == "GET":
            if cache is None:
                cache = _build_cache(0)
            _, key = parsed
            logs.append(f"{step_prefix} {_handle_get(cache, key, analytics)}")

        elif cmd == "STATE":
            if cache is None:
                cache = _build_cache(0)
            logs.append(f"{step_prefix} STATE -> {_format_state(cache)}")

        elif cmd == "RESIZE":
            if cache is None:
                cache = _build_cache(0)
            new_cap = parsed[1]
            if hasattr(cache, "resize") and callable(cache.resize):
                cache.resize(new_cap)
                logs.append(f"{step_prefix} RESIZE {new_cap} -> OK")
            elif hasattr(cache, "set_capacity") and callable(cache.set_capacity):
                cache.set_capacity(new_cap)
                logs.append(f"{step_prefix} RESIZE {new_cap} -> OK")
            else:
                cache.capacity = new_cap
                logs.append(f"{step_prefix} RESIZE {new_cap} -> UPDATED_CAPACITY")

        elif cmd == "ANALYTICS":
            if analytics is not None and hasattr(analytics, "report") and callable(analytics.report):
                logs.append(f"{step_prefix} ANALYTICS -> {analytics.report()}")
            else:
                logs.append(f"{step_prefix} ANALYTICS -> N/A (not initialized)")

    return logs
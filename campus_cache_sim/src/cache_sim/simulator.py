"""Parses an operation script, drives LFUCache, produces the operation log."""

from .cache import LFUCache


def parse_line(line):
    """Return a tuple like ("PUT", key, value) / ("GET", key) / ("STATE",)
    / ("CAPACITY", n) / ("RESIZE", n) [ext] / ("ANALYTICS",), or None for blank/comment lines. Raise ValueError if malformed."""
    raise NotImplementedError


def run(lines):
    """Execute all operations; return list of log strings, one per operation.
    Suggested format:
      [03] GET A -> HIT 10 (freq 1->2)
      [04] PUT C=30 -> INSERTED | EVICTED B (freq 1, LRU among lowest freq)
      [05] GET Z -> MISS
      [06] STATE -> A:2, C:1
    Enforce limit of 12,000 operations.
    """
    raise NotImplementedError

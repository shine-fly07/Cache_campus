"""LFU cache with LRU tie-breaking. GET/PUT must not scan the cache.
Uses ONLY our own HashMap and DoublyLinkedList (see docs/RULES_COMPLIANCE.md)."""

from .node import Node, DoublyLinkedList
from .hashmap import HashMap


class LFUCache:
    def __init__(self, capacity):
        if not 0 <= capacity <= 200:
            raise ValueError("capacity must be between 0 and 200")
        self.capacity = capacity
        self.size = 0
        self.key_map = HashMap()    # key  -> Node
        self.freq_map = HashMap()   # freq -> DoublyLinkedList
        self.min_freq = 0

    def get(self, key):
        """Return (hit: bool, value, old_freq, new_freq). Miss changes nothing."""
        raise NotImplementedError

    def put(self, key, value):
        """Insert or update. Return a dict, e.g.
        {"action": "inserted"|"updated"|"ignored",
         "evicted": None | {"key":..., "freq":..., "reason": "..."}}
        """
        raise NotImplementedError

    def state(self):
        """Return [(key, freq), ...] ordered by freq asc, then LRU -> MRU.
        O(displayed items) only."""
        raise NotImplementedError

    # ---- optional extension hooks ----
    def resize(self, new_capacity):
        """EXTENSION: live capacity change; evict (with reasons) if shrinking."""
        raise NotImplementedError

    # ---- helpers ----
    def _touch(self, node):
        """Move node from freq list f to f+1 as MRU; update min_freq if list f emptied."""
        raise NotImplementedError

    def _evict(self):
        """Remove LRU node of the min_freq list; return (key, freq)."""
        raise NotImplementedError

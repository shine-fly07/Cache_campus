"""EXTENSION (optional): eviction analytics. Hand-rolled counters only."""


class Analytics:
    def __init__(self):
        # TODO: hits, misses, evictions, per-frequency eviction counts,
        #       longest-lived key, hit ratio
        raise NotImplementedError

    def record_hit(self): raise NotImplementedError
    def record_miss(self): raise NotImplementedError
    def record_eviction(self, key, freq): raise NotImplementedError
    def report(self):
        """Return text summary (shown via an ANALYTICS command)."""
        raise NotImplementedError

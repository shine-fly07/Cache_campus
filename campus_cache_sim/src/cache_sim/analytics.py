"""EXTENSION (optional): eviction analytics. Hand-rolled counters only."""

from .hashmap import HashMap


class Analytics:
    """Tracks cache hits, misses, hit ratio, and per-frequency eviction metrics."""

    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.evictions_by_freq = HashMap()
        self._insert_seq = HashMap()
        self._op_seq = 0
        self.longest_lived_key = None
        self._longest_lived_score = -1
        self.last_evicted = None

    def record_hit(self, key=None):
        """Record a cache hit (optionally with key for access tracking). O(1)."""
        self.hits += 1
        self._op_seq += 1

    def record_miss(self):
        """Record a cache miss. O(1)."""
        self.misses += 1
        self._op_seq += 1

    def record_insert(self, key):
        """Optional hook to record when a key entered the cache for lifetime tracking. O(1) avg."""
        self._op_seq += 1
        self._insert_seq.put(key, self._op_seq)

    def record_eviction(self, key, freq):
        """Record an eviction event along with the victim's frequency. O(1) avg."""
        self.evictions += 1
        self._op_seq += 1

        prev_count = self.evictions_by_freq.get(freq, 0)
        self.evictions_by_freq.put(freq, prev_count + 1)
        self.last_evicted = (key, freq)

        if self._insert_seq.contains(key):
            inserted_at = self._insert_seq.remove(key)
            score = self._op_seq - inserted_at
        else:
            score = freq

        if score > self._longest_lived_score:
            self._longest_lived_score = score
            self.longest_lived_key = key

    def hit_ratio(self):
        """Return hits / (hits + misses), or 0.0 when no lookups have occurred."""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total

    def eviction_count_for_freq(self, freq):
        """Return how many evictions occurred at the given frequency."""
        return self.evictions_by_freq.get(freq, 0)

    def _sorted_freq_items(self):
        """Return [(freq, count), ...] sorted ascending by freq without built-in sorted()."""
        pairs = list(self.evictions_by_freq.items())
        for i in range(1, len(pairs)):
            cur = pairs[i]
            j = i - 1
            while j >= 0 and pairs[j][0] > cur[0]:
                pairs[j + 1] = pairs[j]
                j -= 1
            pairs[j + 1] = cur
        return pairs

    def report(self):
        """Return text summary (shown via an ANALYTICS command)."""
        total = self.hits + self.misses
        ratio_pct = self.hit_ratio() * 100.0
        freq_pairs = self._sorted_freq_items()
        if freq_pairs:
            freq_summary = ", ".join(f"freq {f}: {c}" for f, c in freq_pairs)
        else:
            freq_summary = "none"

        longest = (
            f"{self.longest_lived_key} (score {self._longest_lived_score})"
            if self.longest_lived_key is not None
            else "none"
        )

        lines = [
            f"Hits: {self.hits} | Misses: {self.misses} | Lookups: {total} | Hit Ratio: {ratio_pct:.1f}%",
            f"Evictions: {self.evictions} ({freq_summary})",
            f"Longest-lived evicted key: {longest}",
        ]
        return "\n".join(lines)

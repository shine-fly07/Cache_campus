"""Hand-written hash map (separate chaining) so the core never relies on
built-in dict/OrderedDict. Keys: short strings or ints."""


class HashMap:
    """Separate-chaining hash map with custom hashing and 0.75-load-factor resize."""

    LOAD_FACTOR_LIMIT = 0.75

    def __init__(self, initial_buckets=64):
        if isinstance(initial_buckets, bool) or not isinstance(initial_buckets, int) or initial_buckets < 1:
            raise ValueError("initial_buckets must be a positive integer")
        self._buckets = [[] for _ in range(initial_buckets)]
        self._size = 0

    def _raw_hash(self, key):
        """Compute an unreduced non-negative integer hash without built-in hash()."""
        if isinstance(key, bool):
            return 0x9E3779B97F4A7C15 if key else 0x517CC1B727220A95

        if isinstance(key, int):
            # Fold arbitrary-width integers into 64 bits, then apply SplitMix64 mixing.
            val = key if key >= 0 else (-key ^ 0x5555555555555555)
            x = val & 0xFFFFFFFFFFFFFFFF
            rest = val >> 64
            while rest:
                x ^= rest & 0xFFFFFFFFFFFFFFFF
                rest >>= 64
            x = ((x ^ (x >> 30)) * 0xBF58476D1CE4E5B9) & 0xFFFFFFFFFFFFFFFF
            x = ((x ^ (x >> 27)) * 0x94D049BB133111EB) & 0xFFFFFFFFFFFFFFFF
            return x ^ (x >> 31)

        if isinstance(key, str):
            # 64-bit FNV-1a rolling hash over Unicode code points.
            h = 14695981039346656037
            for ch in key:
                h ^= ord(ch)
                h = (h * 1099511628211) & 0xFFFFFFFFFFFFFFFF
            return h

        raise TypeError(f"Unsupported key type: {type(key).__name__}")

    def _hash(self, key):
        """Map key to a bucket index in [0, len(self._buckets) - 1]."""
        return self._raw_hash(key) % len(self._buckets)

    @staticmethod
    def _keys_equal(a, b):
        # Prevent bool (True/False) from matching int (1/0).
        return (isinstance(a, bool) is isinstance(b, bool)) and a == b

    def _find_entry(self, key):
        bucket = self._buckets[self._hash(key)]
        for i, entry in enumerate(bucket):
            if self._keys_equal(entry[0], key):
                return bucket, i, entry
        return bucket, -1, None

    def get(self, key, default=None):
        """Return value for key if present, else default. O(1) average."""
        _, _, entry = self._find_entry(key)
        return entry[1] if entry is not None else default

    def put(self, key, value):
        """Insert or update key -> value; resize when load factor exceeds 0.75. O(1) average."""
        bucket, idx, entry = self._find_entry(key)
        if idx != -1:
            entry[1] = value
            return

        bucket.append([key, value])
        self._size += 1
        if self._size / len(self._buckets) > self.LOAD_FACTOR_LIMIT:
            self._resize()

    def remove(self, key):
        """Remove key and return its value, or None if absent. O(1) average."""
        bucket, idx, entry = self._find_entry(key)
        if idx == -1:
            return None

        val = entry[1]
        # Swap with last element in the chain so removal stays O(1).
        bucket[idx] = bucket[-1]
        bucket.pop()
        self._size -= 1
        return val

    def contains(self, key):
        """Return True if key is present in the map. O(1) average."""
        _, idx, _ = self._find_entry(key)
        return idx != -1

    def __len__(self):
        return self._size

    def __contains__(self, key):
        return self.contains(key)

    def __getitem__(self, key):
        _, _, entry = self._find_entry(key)
        if entry is None:
            raise KeyError(key)
        return entry[1]

    def __setitem__(self, key, value):
        self.put(key, value)

    def __delitem__(self, key):
        bucket, idx, _ = self._find_entry(key)
        if idx == -1:
            raise KeyError(key)
        bucket[idx] = bucket[-1]
        bucket.pop()
        self._size -= 1

    def load_factor(self):
        """Return current size / bucket_count ratio."""
        return self._size / len(self._buckets)

    def bucket_count(self):
        """Return current number of hash buckets."""
        return len(self._buckets)

    def keys(self):
        """Yield all keys across buckets."""
        for bucket in self._buckets:
            for entry in bucket:
                yield entry[0]

    def values(self):
        """Yield all values across buckets."""
        for bucket in self._buckets:
            for entry in bucket:
                yield entry[1]

    def items(self):
        """Yield (key, value) pairs across buckets."""
        for bucket in self._buckets:
            for entry in bucket:
                yield (entry[0], entry[1])

    def clear(self):
        """Remove all entries while retaining current bucket capacity."""
        self._buckets = [[] for _ in range(len(self._buckets))]
        self._size = 0

    def _resize(self):
        """Double bucket count and rehash all entries."""
        new_cap = len(self._buckets) * 2
        new_buckets = [[] for _ in range(new_cap)]
        for bucket in self._buckets:
            for entry in bucket:
                idx = self._raw_hash(entry[0]) % new_cap
                new_buckets[idx].append(entry)
        self._buckets = new_buckets

"""Hand-written hash map (separate chaining) so the core never relies on
built-in dict/OrderedDict. Keys: short strings or ints."""


class HashMap:
    def __init__(self, initial_buckets=64):
        # TODO: buckets = list of chains, size = 0
        raise NotImplementedError

    def _hash(self, key):
        """TODO: own hash function (e.g. polynomial rolling hash for str, mod for int)."""
        raise NotImplementedError

    def get(self, key, default=None):
        raise NotImplementedError

    def put(self, key, value):
        raise NotImplementedError

    def remove(self, key):
        """Return removed value or None."""
        raise NotImplementedError

    def contains(self, key):
        raise NotImplementedError

    def __len__(self):
        raise NotImplementedError

    def _resize(self):
        """TODO: grow + rehash when load factor > 0.75 (keeps average O(1))."""
        raise NotImplementedError

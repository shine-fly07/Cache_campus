class ReferenceCache:
    def __init__(self, capacity):
        if not 0 <= capacity <= 200:
            raise ValueError("capacity must be between 0 and 200")

        self.capacity = capacity
        self.items = {}
        self.clock = 0
    def _time(self):
        self.clock += 1
        return self.clock

    def get(self, key):
        if key not in self.items:
            return False, None, 0, 0

        item = self.items[key]
        old_freq = item["freq"]

        item["freq"] += 1
        item["last_used"] = self._time()

        return True, item["value"], old_freq, item["freq"]

    def put(self, key, value):
        if self.capacity == 0:
            return {"action": "ignored", "evicted": None}

        # Updating an existing key
        if key in self.items:
            item = self.items[key]
            item["value"] = value
            item["freq"] += 1
            item["last_used"] = self._time()

            return {"action": "updated", "evicted": None}

        # Evict when cache is full
        evicted = None

        if len(self.items) >= self.capacity:
            victim_key = min(
                self.items,
                key=lambda k: (
                    self.items[k]["freq"],
                    self.items[k]["last_used"]
                )
            )

            victim = self.items[victim_key]

            evicted = {
                "key": victim_key,
                "freq": victim["freq"],
                "reason": "LFU; LRU tie-break"
            }

            del self.items[victim_key]

        # Insert new key with frequency 1
        self.items[key] = {
            "value": value,
            "freq": 1,
            "last_used": self._time()
        }

        return {
            "action": "inserted",
            "evicted": evicted
        }

    def state(self):
        ordered_keys = sorted(
            self.items,
            key=lambda k: (
                self.items[k]["freq"],
                self.items[k]["last_used"]
            )
        )

        return [
            (key, self.items[key]["freq"])
            for key in ordered_keys
        ]
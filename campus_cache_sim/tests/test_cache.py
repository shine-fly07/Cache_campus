


import unittest
from src.cache_sim.cache import LFUCache


class TestLFUCache(unittest.TestCase):

    def test_example_from_spec(self):
        """Capacity 2: PUT A, PUT B, GET A, PUT C."""
        cache = LFUCache(2)

        cache.put("A", "File1")
        cache.put("B", "File2")
        cache.get("A")

        result = cache.put("C", "File3")

        self.assertEqual(result["evicted"][0], "B")
        self.assertEqual(cache.state(), [("C", 1), ("A", 2)])

    def test_tie_breaks_by_lru(self):
        cache = LFUCache(2)

        cache.put("A", "File1")
        cache.put("B", "File2")

        result = cache.put("C", "File3")

        self.assertEqual(result["evicted"][0], "A")
        self.assertEqual(result["evicted"][1], 1)
        self.assertEqual(result["evicted"][2], "LFU + LRU tie-break")

    def test_put_existing_updates_and_counts_as_access(self):
        cache = LFUCache(2)

        cache.put("A", "OldValue")
        result = cache.put("A", "NewValue")

        self.assertEqual(result["action"], "updated")
        self.assertEqual(cache.get("A"), (True, "NewValue", 2, 3))

    def test_missed_get_does_not_insert(self):
        cache = LFUCache(2)

        cache.put("A", "File1")

        before = cache.state()
        result = cache.get("B")

        self.assertEqual(result, (False, None, None, None))
        self.assertEqual(cache.state(), before)
        self.assertEqual(cache.size, 1)

    def test_zero_capacity_ignores_puts(self):
        cache = LFUCache(0)

        result = cache.put("A", "File1")

        self.assertEqual(result["action"], "ignored")
        self.assertEqual(cache.size, 0)
        self.assertEqual(cache.state(), [])

    def test_repeated_updates_raise_frequency(self):
        cache = LFUCache(2)

        cache.put("A", "File1")
        cache.put("A", "File2")
        cache.put("A", "File3")

        self.assertEqual(cache.state(), [("A", 3)])
        self.assertEqual(cache.get("A"), (True, "File3", 3, 4))

    def test_new_key_resets_min_freq_to_one(self):
        cache = LFUCache(2)

        cache.put("A", "File1")
        cache.get("A")
        cache.get("A")

        self.assertEqual(cache.min_freq, 3)

        cache.put("B", "File2")

        self.assertEqual(cache.min_freq, 1)

    def test_invalid_capacity(self):
        with self.assertRaises(ValueError):
            LFUCache(201)


if __name__ == "__main__":
    unittest.main()

import unittest
from src.cache_sim.cache import LFUCache


class TestLFUCache(unittest.TestCase):
    def test_example_from_spec(self):
        """cap 2: PUT A, PUT B, GET A, PUT C -> B evicted; A freq 2, C freq 1."""
        self.skipTest("TODO")

    def test_tie_breaks_by_lru(self):
        self.skipTest("TODO")

    def test_put_existing_updates_and_counts_as_access(self):
        self.skipTest("TODO")

    def test_missed_get_does_not_insert(self):
        self.skipTest("TODO")

    def test_zero_capacity_ignores_puts(self):
        self.skipTest("TODO")

    def test_repeated_updates_raise_frequency(self):
        self.skipTest("TODO")

    def test_new_key_resets_min_freq_to_one(self):
        self.skipTest("TODO")

    def test_invalid_capacity(self):
        with self.assertRaises(ValueError):
            LFUCache(201)


if __name__ == "__main__":
    unittest.main()

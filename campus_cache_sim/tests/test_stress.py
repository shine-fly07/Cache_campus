import unittest
import random

from tests.reference_cache import ReferenceCache


class TestStress(unittest.TestCase):

    def test_reference_cache_random_operations(self):
        random.seed(42)

        cache = ReferenceCache(5)

        for _ in range(500):
            key = random.choice("ABCDEFGHIJ")

            if random.random() < 0.5:
                # Random PUT
                value = random.randint(1, 1000)
                cache.put(key, value)
            else:
                # Random GET
                cache.get(key)

            # Cache must never exceed its capacity
            self.assertLessEqual(len(cache.items), 5)

            # Every stored frequency must be positive
            for item in cache.items.values():
                self.assertGreaterEqual(item["freq"], 1)

            # Keys must be unique
            state = cache.state()
            keys = [key for key, freq in state]
            self.assertEqual(len(keys), len(set(keys)))


if __name__ == "__main__":
    unittest.main()
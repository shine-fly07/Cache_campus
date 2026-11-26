import unittest
from tests.reference_cache import ReferenceCache

class TestReferenceCache(unittest.TestCase):

    def test_insert_and_get(self):
        cache = ReferenceCache(2)

        cache.put("A", 10)

        result = cache.get("A")

        self.assertEqual(result, (True, 10, 1, 2))

    def test_missing_key(self):
        cache = ReferenceCache(2)

        result = cache.get("X")

        self.assertEqual(result, (False, None, 0, 0))
        self.assertEqual(cache.state(), [])

    def test_update_existing_key(self):
        cache = ReferenceCache(2)

        cache.put("A", 10)
        result = cache.put("A", 50)

        self.assertEqual(result["action"], "updated")
        self.assertEqual(cache.get("A"), (True, 50, 2, 3))

    def test_lru_tie_break(self):
        cache = ReferenceCache(2)

        cache.put("A", 10)
        cache.put("B", 20)

        result = cache.put("C", 30)

        self.assertEqual(result["evicted"]["key"], "A")
        self.assertEqual(cache.state(), [("B", 1), ("C", 1)])

    def test_zero_capacity(self):
        cache = ReferenceCache(0)

        result = cache.put("A", 10)

        self.assertEqual(result["action"], "ignored")
        self.assertEqual(cache.state(), [])

    def test_new_key_frequency_is_one(self):
        cache = ReferenceCache(2)

        cache.put("A", 10)

        self.assertEqual(cache.state(), [("A", 1)])

if __name__ == "__main__":
    unittest.main()
import unittest
from src.cache_sim.hashmap import HashMap


class TestHashMap(unittest.TestCase):
    def test_put_get_remove(self):
        hm = HashMap()
        self.assertEqual(len(hm), 0)
        self.assertFalse(hm.contains("A"))
        self.assertIsNone(hm.get("A"))
        self.assertEqual(hm.get("A", -1), -1)

        hm.put("A", 10)
        hm.put("B", 20)
        hm.put(1, "freq1")

        self.assertEqual(len(hm), 3)
        self.assertTrue(hm.contains("A"))
        self.assertTrue("B" in hm)
        self.assertEqual(hm.get("A"), 10)
        self.assertEqual(hm.get("B"), 20)
        self.assertEqual(hm.get(1), "freq1")

        self.assertEqual(hm.remove("A"), 10)
        self.assertFalse(hm.contains("A"))
        self.assertIsNone(hm.get("A"))
        self.assertIsNone(hm.remove("A"))
        self.assertEqual(len(hm), 2)

    def test_overwrite_existing_key(self):
        hm = HashMap(initial_buckets=4)
        hm.put("file1", 100)
        hm.put("file1", 200)
        hm.put("file1", 300)

        self.assertEqual(len(hm), 1)
        self.assertEqual(hm.get("file1"), 300)
        self.assertEqual(hm.bucket_count(), 4)

    def test_collisions_handled(self):
        # Single bucket forces every key into the exact same chain.
        hm = HashMap(initial_buckets=1)
        # Prevent auto-resize by testing inside 1 bucket via direct chaining check,
        # or test with small capacity after resize by probing two colliding keys in 2 buckets.
        hm2 = HashMap(initial_buckets=8)
        # Find keys that collide in 8 buckets using _hash.
        colliding = []
        i = 0
        while len(colliding) < 4:
            k = f"key_{i}"
            if hm2._hash(k) == 0:
                colliding.append(k)
            i += 1

        for idx, k in enumerate(colliding):
            hm2.put(k, idx)

        self.assertEqual(hm2.bucket_count(), 8)  # 4/8 = 0.5 <= 0.75, no resize yet
        self.assertEqual(len(hm2), 4)
        for idx, k in enumerate(colliding):
            self.assertEqual(hm2.get(k), idx)

        # Overwrite middle item in chain
        hm2.put(colliding[1], 999)
        self.assertEqual(hm2.get(colliding[1]), 999)
        self.assertEqual(len(hm2), 4)

        # Remove head, middle, and tail items of chain
        self.assertEqual(hm2.remove(colliding[0]), 0)
        self.assertEqual(hm2.remove(colliding[2]), 2)
        self.assertEqual(hm2.remove(colliding[3]), 3)
        self.assertEqual(hm2.get(colliding[1]), 999)
        self.assertEqual(len(hm2), 1)

        # Also verify single-bucket map still preserves everything across resizes
        hm.put("a", 1)
        hm.put("b", 2)
        hm.put("c", 3)
        self.assertEqual((hm.get("a"), hm.get("b"), hm.get("c")), (1, 2, 3))

    def test_resize_keeps_all_entries(self):
        hm = HashMap(initial_buckets=4)
        # 3 / 4 = 0.75 -> should NOT resize at exactly 0.75
        for i in range(3):
            hm.put(f"k{i}", i * 10)
        self.assertEqual(hm.bucket_count(), 4)
        self.assertEqual(hm.load_factor(), 0.75)

        # 4 / 4 = 1.0 > 0.75 -> triggers resize to 8 buckets
        hm.put("k3", 30)
        self.assertEqual(hm.bucket_count(), 8)
        self.assertEqual(len(hm), 4)

        # Push through multiple resizes
        for i in range(4, 150):
            hm.put(f"k{i}", i * 10)

        self.assertEqual(len(hm), 150)
        self.assertLessEqual(hm.load_factor(), 0.75)
        for i in range(150):
            self.assertEqual(hm.get(f"k{i}"), i * 10)

    def test_int_keys_and_multiples_distribution(self):
        hm = HashMap(initial_buckets=64)
        # Multiples of 64 should not all land in bucket 0 thanks to bit mixing.
        buckets = {hm._hash(i * 64) for i in range(32)}
        self.assertGreater(len(buckets), 16)

        for i in range(-20, 20):
            hm.put(i, i * i)
        for i in range(-20, 20):
            self.assertEqual(hm.get(i), i * i)

    def test_none_values_and_bool_int_distinction(self):
        hm = HashMap()
        hm.put("empty", None)
        self.assertTrue(hm.contains("empty"))
        self.assertIsNone(hm.get("empty", "fallback"))
        self.assertIsNone(hm["empty"])

        hm.put(1, "int_one")
        hm.put(True, "bool_true")
        self.assertEqual(hm.get(1), "int_one")
        self.assertEqual(hm.get(True), "bool_true")
        self.assertEqual(len(hm), 3)

    def test_dunder_and_iteration_helpers(self):
        hm = HashMap(initial_buckets=4)
        hm["x"] = 1
        hm["y"] = 2
        self.assertEqual(hm["x"], 1)
        self.assertEqual(set(hm.keys()), {"x", "y"})
        self.assertEqual(set(hm.values()), {1, 2})
        self.assertEqual(set(hm.items()), {("x", 1), ("y", 2)})

        del hm["x"]
        self.assertFalse("x" in hm)
        with self.assertRaises(KeyError):
            _ = hm["x"]
        with self.assertRaises(KeyError):
            del hm["x"]

        hm.clear()
        self.assertEqual(len(hm), 0)
        self.assertEqual(list(hm.items()), [])

    def test_invalid_inputs_raise(self):
        with self.assertRaises(ValueError):
            HashMap(0)
        with self.assertRaises(ValueError):
            HashMap(-4)
        with self.assertRaises(ValueError):
            HashMap(True)

        hm = HashMap()
        with self.assertRaises(TypeError):
            hm.put(["unhashable"], 1)
        with self.assertRaises(TypeError):
            hm.get(None)

    def test_large_scale_put_get_remove(self):
        hm = HashMap()
        n = 3000
        for i in range(n):
            hm.put(f"doc_{i}", i)
        self.assertEqual(len(hm), n)
        self.assertLessEqual(hm.load_factor(), 0.75)

        for i in range(0, n, 2):
            self.assertEqual(hm.remove(f"doc_{i}"), i)
        self.assertEqual(len(hm), n // 2)

        for i in range(n):
            if i % 2 == 0:
                self.assertFalse(hm.contains(f"doc_{i}"))
            else:
                self.assertEqual(hm.get(f"doc_{i}"), i)


if __name__ == "__main__":
    unittest.main()

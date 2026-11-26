import unittest


class TestStress(unittest.TestCase):
    def test_matches_bruteforce_reference_on_random_ops(self):
        """Compare LFUCache vs a slow O(n) reference (tests-only; reference may use
        built-ins because it is NOT the solution)."""
        self.skipTest("TODO")

    def test_12000_ops_capacity_200_is_fast(self): self.skipTest("TODO")


if __name__ == "__main__":
    unittest.main()

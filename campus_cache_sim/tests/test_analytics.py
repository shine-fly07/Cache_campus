import unittest
from src.cache_sim.analytics import Analytics


class TestAnalytics(unittest.TestCase):
    def test_initial_state_and_zero_hit_ratio(self):
        a = Analytics()
        self.assertEqual(a.hits, 0)
        self.assertEqual(a.misses, 0)
        self.assertEqual(a.evictions, 0)
        self.assertEqual(a.hit_ratio(), 0.0)
        self.assertIsNone(a.longest_lived_key)

        text = a.report()
        self.assertIn("Hits: 0", text)
        self.assertIn("Hit Ratio: 0.0%", text)
        self.assertIn("Evictions: 0", text)

    def test_hits_misses_and_hit_ratio(self):
        a = Analytics()
        a.record_hit()
        a.record_hit()
        a.record_miss()
        self.assertEqual(a.hits, 2)
        self.assertEqual(a.misses, 1)
        self.assertAlmostEqual(a.hit_ratio(), 2 / 3)

    def test_evictions_per_frequency_and_report(self):
        a = Analytics()
        a.record_eviction("B", 1)
        a.record_eviction("D", 3)
        a.record_eviction("C", 1)

        self.assertEqual(a.evictions, 3)
        self.assertEqual(a.eviction_count_for_freq(1), 2)
        self.assertEqual(a.eviction_count_for_freq(3), 1)
        self.assertEqual(a.eviction_count_for_freq(2), 0)
        self.assertEqual(a.longest_lived_key, "D")

        report = a.report()
        self.assertIn("Evictions: 3 (freq 1: 2, freq 3: 1)", report)
        self.assertIn("Longest-lived evicted key: D", report)

    def test_longest_lived_key_with_insert_tracking(self):
        a = Analytics()
        a.record_insert("A")
        a.record_insert("B")
        a.record_hit("A")
        a.record_miss()
        a.record_eviction("B", 1)  # B lived across A's insert, hit, miss
        a.record_insert("C")
        a.record_eviction("C", 2)  # C lived 1 step
        a.record_eviction("A", 2)  # A lived from step 1 to end

        self.assertEqual(a.longest_lived_key, "A")
        self.assertEqual(a.eviction_count_for_freq(1), 1)
        self.assertEqual(a.eviction_count_for_freq(2), 2)


if __name__ == "__main__":
    unittest.main()

import unittest
from unittest.mock import patch

from src.cache_sim.simulator import MAX_OPERATIONS, parse_line, run


class TestSimulator(unittest.TestCase):
    def test_parse_valid_commands_and_comments(self):
        self.assertIsNone(parse_line(""))
        self.assertIsNone(parse_line("   # full-line comment  "))
        self.assertEqual(parse_line("CAPACITY 3 # set cap"), ("CAPACITY", 3))
        self.assertEqual(parse_line("PUT X 10"), ("PUT", "X", "10"))
        self.assertEqual(parse_line("GET X"), ("GET", "X"))
        self.assertEqual(parse_line("STATE"), ("STATE",))
        self.assertEqual(parse_line("RESIZE 5"), ("RESIZE", 5))
        self.assertEqual(parse_line("ANALYTICS"), ("ANALYTICS",))

    def test_parse_malformed_lines_raises(self):
        bad_lines = [
            "PUT ONLY_ONE_ARG",
            "PUT A B EXTRA",
            "GET",
            "GET A B",
            "CAPACITY",
            "CAPACITY -1",
            "CAPACITY abc",
            "STATE extra",
            "UNKNOWN_CMD 1",
        ]
        for line in bad_lines:
            with self.subTest(line=line):
                with self.assertRaises(ValueError):
                    parse_line(line)

    @patch("src.cache_sim.simulator.LFUCache", side_effect=NotImplementedError)
    def test_run_with_fake_cache_and_state_only_on_request(self, _mock_cache):
        script = [
            "# Unseen demo",
            "CAPACITY 3",
            "PUT X 1",
            "PUT Y 2",
            "PUT Z 3",
            "GET X",
            "PUT W 4",
            "GET Q",
            "STATE",
        ]
        logs = run(script)
        self.assertEqual(len(logs), 8)
        state_lines = [line for line in logs if "STATE ->" in line]
        self.assertEqual(len(state_lines), 1)
        self.assertIn("EVICTED", logs[5])
        self.assertIn("MISS", logs[6])

    @patch("src.cache_sim.simulator.LFUCache", side_effect=NotImplementedError)
    def test_12000_operation_limit_enforced(self, _mock_cache):
        ops = ["STATE"] * MAX_OPERATIONS
        self.assertEqual(len(run(ops)), MAX_OPERATIONS)

        with self.assertRaises(ValueError):
            run(ops + ["STATE"])


if __name__ == "__main__":
    unittest.main()

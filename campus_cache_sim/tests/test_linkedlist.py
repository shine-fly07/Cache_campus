import unittest
from src.cache_sim.node import Node, DoublyLinkedList


class TestDoublyLinkedList(unittest.TestCase):
    def test_push_front_order(self):
        dll = DoublyLinkedList()
        a = Node("A", 1)
        b = Node("B", 2)
        c = Node("C", 3)
        dll.push_front(a)
        dll.push_front(b)
        dll.push_front(c)

        self.assertEqual(len(dll), 3)
        self.assertEqual([n.key for n in dll], ["C", "B", "A"])
        self.assertIs(dll.pop_back(), a)
        self.assertIs(dll.pop_back(), b)
        self.assertIs(dll.pop_back(), c)
        self.assertEqual(len(dll), 0)

    def test_remove_middle_head_tail(self):
        dll = DoublyLinkedList()
        a = Node("A", 1)
        b = Node("B", 2)
        c = Node("C", 3)
        dll.push_front(a)
        dll.push_front(b)
        dll.push_front(c)  # MRU -> LRU: C, B, A

        # Remove middle (B)
        removed = dll.remove(b)
        self.assertIs(removed, b)
        self.assertIsNone(b.prev)
        self.assertIsNone(b.next)
        self.assertEqual([n.key for n in dll], ["C", "A"])
        self.assertEqual(len(dll), 2)

        # Remove head-side MRU (C)
        dll.remove(c)
        self.assertEqual([n.key for n in dll], ["A"])
        self.assertEqual(len(dll), 1)

        # Remove remaining tail-side LRU (A)
        dll.remove(a)
        self.assertEqual(list(dll), [])
        self.assertEqual(len(dll), 0)
        self.assertTrue(dll.is_empty())

    def test_pop_back_empty_returns_none(self):
        dll = DoublyLinkedList()
        self.assertIsNone(dll.pop_back())
        self.assertTrue(dll.is_empty())

        n = Node("X", 10)
        dll.push_front(n)
        self.assertIs(dll.pop_back(), n)
        self.assertIsNone(dll.pop_back())

    def test_iteration_order_mru_to_lru(self):
        dll = DoublyLinkedList()
        nodes = [Node(k, i) for i, k in enumerate(["K1", "K2", "K3", "K4"])]
        for node in nodes:
            dll.push_front(node)

        self.assertEqual([n.key for n in dll], ["K4", "K3", "K2", "K1"])
        self.assertEqual([n.key for n in reversed(dll)], ["K1", "K2", "K3", "K4"])

    def test_peek_front_and_back(self):
        dll = DoublyLinkedList()
        self.assertIsNone(dll.peek_front())
        self.assertIsNone(dll.peek_back())

        first = Node("first", 1)
        second = Node("second", 2)
        dll.push_front(first)
        dll.push_front(second)

        self.assertIs(dll.peek_front(), second)
        self.assertIs(dll.peek_back(), first)
        self.assertEqual(len(dll), 2)

    def test_reinsert_after_remove_or_pop(self):
        dll1 = DoublyLinkedList()
        dll2 = DoublyLinkedList()
        n = Node("file", 42, freq=1)
        dll1.push_front(n)
        dll1.remove(n)
        n.freq += 1
        dll2.push_front(n)

        self.assertEqual(len(dll1), 0)
        self.assertEqual(len(dll2), 1)
        self.assertIs(dll2.peek_front(), n)

    def test_invalid_operations_raise(self):
        dll = DoublyLinkedList()
        n = Node("A", 1)

        with self.assertRaises(ValueError):
            dll.push_front(None)
        with self.assertRaises(ValueError):
            dll.push_front(dll.head)
        with self.assertRaises(ValueError):
            dll.push_front(dll.tail)
        with self.assertRaises(ValueError):
            dll.remove(n)
        with self.assertRaises(ValueError):
            dll.remove(dll.head)

        dll.push_front(n)
        with self.assertRaises(ValueError):
            dll.push_front(n)


if __name__ == "__main__":
    unittest.main()

"""Linked-list building blocks for the LFU cache."""


class Node:
    """One cached file. Lives in the list for its current frequency."""

    __slots__ = ("key", "value", "freq", "prev", "next")

    def __init__(self, key, value, freq=1):
        self.key = key
        self.value = value
        self.freq = freq
        self.prev = None
        self.next = None


class DoublyLinkedList:
    """Sentinel-based list. Head side = most recent, tail side = least recent."""

    def __init__(self):
        self.head = Node(None, None, 0)
        self.tail = Node(None, None, 0)
        self.head.next = self.tail
        self.tail.prev = self.head
        self._size = 0

    def __len__(self):
        return self._size

    def is_empty(self):
        """Return True if the list contains no data nodes. O(1)."""
        return self._size == 0

    def push_front(self, node):
        """Insert node as most recently used. O(1)."""
        if node is None or node is self.head or node is self.tail:
            raise ValueError("Cannot insert None or a sentinel node")
        if node.prev is not None or node.next is not None:
            raise ValueError("Node is already linked in a list")

        first = self.head.next
        node.prev = self.head
        node.next = first
        self.head.next = node
        first.prev = node
        self._size += 1

    def remove(self, node):
        """Unlink node from anywhere in the list. O(1)."""
        if node is None or node is self.head or node is self.tail:
            raise ValueError("Cannot remove None or a sentinel node")
        if node.prev is None or node.next is None:
            raise ValueError("Node is not linked in a list")

        node.prev.next = node.next
        node.next.prev = node.prev
        node.prev = None
        node.next = None
        self._size -= 1
        return node

    def pop_back(self):
        """Remove and return the least recently used node (None if empty). O(1)."""
        if self._size == 0:
            return None
        return self.remove(self.tail.prev)

    def peek_front(self):
        """Return the most recently used node without removing it (None if empty). O(1)."""
        if self._size == 0:
            return None
        return self.head.next

    def peek_back(self):
        """Return the least recently used node without removing it (None if empty). O(1)."""
        if self._size == 0:
            return None
        return self.tail.prev

    def __iter__(self):
        """Iterate most -> least recent (used by STATE only)."""
        cur = self.head.next
        while cur is not self.tail:
            nxt = cur.next
            yield cur
            cur = nxt

    def __reversed__(self):
        """Iterate least -> most recent (O(n) helper for LRU-to-MRU display)."""
        cur = self.tail.prev
        while cur is not self.head:
            prv = cur.prev
            yield cur
            cur = prv

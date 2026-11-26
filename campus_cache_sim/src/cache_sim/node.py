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
        # TODO: create head/tail sentinels, link them, set size = 0
        raise NotImplementedError

    def __len__(self):
        raise NotImplementedError

    def push_front(self, node):
        """Insert node as most recently used. O(1)."""
        raise NotImplementedError

    def remove(self, node):
        """Unlink node from anywhere in the list. O(1)."""
        raise NotImplementedError

    def pop_back(self):
        """Remove and return the least recently used node (None if empty)."""
        raise NotImplementedError

    def __iter__(self):
        """Iterate most -> least recent (used by STATE only)."""
        raise NotImplementedError

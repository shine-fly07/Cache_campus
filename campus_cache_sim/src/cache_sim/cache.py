"""LFU cache with LRU tie-breaking. GET/PUT must not scan the cache.
Uses ONLY our own HashMap and DoublyLinkedList (see docs/RULES_COMPLIANCE.md)."""

from .node import Node, DoublyLinkedList
from .hashmap import HashMap


class LFUCache:
    def __init__(self, capacity):
        if not 0 <= capacity <= 200:
            raise ValueError("capacity must be between 0 and 200")
        self.capacity = capacity
        self.size = 0
        self.key_map = HashMap()    # key  -> Node
        self.freq_map = HashMap()   # freq -> DoublyLinkedList
        self.min_freq = 0

    
    def get(self, key):
        """Return (hit, value, old_freq, new_freq)."""

        node = self.key_map.get(key)

        # Key does not exist
        if node is None:
            return (False, None, None, None)

        # Store the old frequency
        old_freq = node.freq

        # Increase frequency and update its position
        self._touch(node)

        new_freq = node.freq

        return (True, node.value, old_freq, new_freq)
    

    
    def put(self, key, value):
        """Insert or update a key-value pair."""

        # Case 1: Zero capacity
        if self.capacity == 0:
            return {
                "action": "ignored",
                "evicted": None
            }

        # Check whether key already exists
        node = self.key_map.get(key)

        # Case 2: Key already exists
        if node is not None:
            node.value = value

            # Updating an existing key counts as an access
            self._touch(node)

            return {
                "action": "updated",
                "evicted": None
            }

        # Case 3: New key and cache is full
        evicted = None

        if self.size == self.capacity:
            evicted = self._evict()

        # Create a new node with frequency 1
        new_node = Node(key, value, 1)

        # Add it to the key map
        self.key_map.put(key, new_node)

        # Get or create the frequency-1 list
        freq_list = self.freq_map.get(1)

        if freq_list is None:
            freq_list = DoublyLinkedList()
            self.freq_map.put(1, freq_list)

        # Insert asmost recently used
        freq_list.push_front(new_node)

        self.size += 1

        # Every new key starts with frequency 1
        self.min_freq = 1

        return {
            "action": "inserted",
            "evicted": evicted
        }

        
    def state(self):
        """Return [(key, freq), ...] ordered by frequency,
        then from LRU to MRU.
        """

        # Get all existing frequencies
        frequencies = list(self.freq_map.keys())

        # Merge Sort without using sorted()
        def merge_sort(arr):
            if len(arr) <= 1:
                return arr

            mid = len(arr) // 2

            left = merge_sort(arr[:mid])
            right = merge_sort(arr[mid:])

            result = []
            i = 0
            j = 0

            while i < len(left) and j < len(right):
                if left[i] <= right[j]:
                    result.append(left[i])
                    i += 1
                else:
                    result.append(right[j])
                    j += 1

            while i < len(left):
                result.append(left[i])
                i += 1

            while j < len(right):
                result.append(right[j])
                j += 1

            return result

        frequencies = merge_sort(frequencies)

        # Build the final cache state
        result = []

        for freq in frequencies:
            freq_list = self.freq_map.get(freq)

            # reversed() gives LRU to MRU
            for node in reversed(freq_list):
                result.append((node.key, node.freq))

        return result
    

    # ---- optional extension hooks ----
    def resize(self, new_capacity):
        """EXTENSION: live capacity change; evict (with reasons) if shrinking."""
        raise NotImplementedError

    # ---- helpers ----
    def _touch(self, node):
        old_freq = node.freq

        # Get the current frequency list
        old_list = self.freq_map.get(old_freq)

        # Remove the node from its current list
        old_list.remove(node)

        # If the old frequency list becomes empty
        if len(old_list) == 0:
            self.freq_map.remove(old_freq)

            # Update minimum frequency
            if self.min_freq == old_freq:
                self.min_freq += 1

        # Increase the node's frequency
        node.freq += 1

        # Get the new frequency list
        new_list = self.freq_map.get(node.freq)

        # Create a new list if it doesn't exist
        if new_list is None:
            new_list = DoublyLinkedList()
            self.freq_map.put(node.freq, new_list)

        # Insert the node as most recently used
        new_list.push_front(node)

    
    def _evict(self):
        """Remove the LRU node from the minimum-frequency list."""

        if self.size == 0:
            return None

        min_list = self.freq_map.get(self.min_freq)

        if min_list is None or min_list.is_empty():
            raise RuntimeError("Minimum frequency list is missing")

        # Check whether multiple nodes have the same minimum frequency
        tie_exists = len(min_list) > 1

        # Remove the LRU node
        victim = min_list.pop_back()

        key = victim.key
        freq = victim.freq

        # Remove the key from the key map
        self.key_map.remove(key)

        self.size -= 1

        # Remove the frequency list if it becomes empty
        if min_list.is_empty():
            self.freq_map.remove(freq)

        # Explain why this node was evicted
        if tie_exists:
            reason = "LFU + LRU tie-break"
        else:
            reason = "LFU"

        return (key, freq, reason)
    

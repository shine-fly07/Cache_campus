# Programming-Guideline Compliance

Rule: no inbuilt shortcut that directly solves the core problem.

| Allowed (plumbing)                         | Not used (would solve the core)               |
|--------------------------------------------|-----------------------------------------------|
| lists/arrays, ints, strings, file I/O      | OrderedDict, functools.lru_cache, cachetools  |
| our own HashMap, DoublyLinkedList classes  | collections.deque as the LRU structure        |
| unittest, random (tests/demo only)         | heapq / sorted() to pick eviction victims     |

- Lookup: hand-written `HashMap` (separate chaining, own hash, own resize).
- Recency: hand-written sentinel `DoublyLinkedList` per frequency.
- Eviction: `min_freq` + tail of that list; never a scan or sort.
- The brute-force reference in tests/ is a checker only, not part of the solution.
- AI assistance is allowed; record where it was used in CONTRIBUTIONS.md.

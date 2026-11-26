# Design Notes

## Structures
- key_map: HashMap key -> Node (own implementation)                (O(1) lookup)
- freq_map: HashMap freq -> DoublyLinkedList  (LRU order inside each frequency)
- min_freq: int                            (which list to evict from, O(1))

## Eviction
Evict tail of freq_map[min_freq] (least frequent, then least recent).

## Complexity
GET/PUT O(1) average; STATE O(n displayed).

## TODO: eviction walkthrough for the demo sequence
## TODO: optional extension (live resize, eviction analytics)

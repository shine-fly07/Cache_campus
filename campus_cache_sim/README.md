# Campus Cloud File Cache Simulator (LFU + LRU tie-break)

Fixed-capacity cache (0-200 keys, <=12,000 ops) with GET/PUT/STATE.
Eviction: least frequently used; ties -> least recently used. GET/PUT are O(1).
All core structures are hand-written (see docs/RULES_COMPLIANCE.md).

## Layout
- src/cache_sim/hashmap.py    Own hash map (chaining, resize)
- src/cache_sim/node.py       Node + DoublyLinkedList (sentinels, O(1))
- src/cache_sim/cache.py      LFUCache (key_map, freq_map, min_freq)
- src/cache_sim/simulator.py  Parse operations, run, build operation log
- src/cache_sim/analytics.py  [extension] eviction analytics
- src/cache_sim/cli.py        Command-line entry point
- tests/                      Unit, tie/update/miss/zero-capacity, stress tests
- demo/sequence.txt           Unseen demo sequence
- docs/                       design.md, RULES_COMPLIANCE.md
- CONTRIBUTIONS.md            Per-member contribution log

## Run
    python -m src.cache_sim.cli demo/sequence.txt
    python -m unittest discover -s tests -t .

## Input format
    CAPACITY 2
    PUT A 10
    GET A
    STATE
    RESIZE 3        # extension
    ANALYTICS       # extension

## Extensions (optional, if time permits)
Live RESIZE, ANALYTICS report, scale to 1,000 keys / 30,000 ops.

# Campus Cloud File Cache Simulator (LFU + LRU tie-break)

Fixed-capacity cache (0–200 keys, <=12,000 ops) with `GET`/`PUT`/`STATE` and an interactive Web UI.
Eviction: least frequently used; ties -> least recently used. `GET`/`PUT` are O(1) on average.
All core structures are hand-written using only Python's standard library (see `docs/RULES_COMPLIANCE.md`).

## Layout
- `pyproject.toml`               Project metadata & entry points (`cache-sim`, `cache-sim-ui`)
- `src/cache_sim/hashmap.py`     Own hash map (FNV-1a / SplitMix64 hash, chaining, resize at >0.75 load)
- `src/cache_sim/node.py`        `Node` + sentinel `DoublyLinkedList` (O(1) push/remove/pop)
- `src/cache_sim/cache.py`       `LFUCache` (`key_map`, `freq_map`, `min_freq`)
- `src/cache_sim/simulator.py`   Operation parser, script runner, operation log builder
- `src/cache_sim/analytics.py`   [extension] Hand-rolled hit/miss/eviction & lifetime analytics
- `src/cache_sim/cli.py`         Command-line entry point
- `src/cache_sim/ui.py`          Interactive Web UI server (`http.server`) & `CacheSession` API
- `src/cache_sim/static/index.html` Offline browser dashboard for live cache visualization
- `tests/`                       Unit, reference, stress & UI tests (`test_linkedlist`, `test_hashmap`, `test_cache`, `test_simulator`, `test_analytics`, `test_ui`, `reference_cache`, `test_reference_cache`, `test_stress`)
- `demo/sequence.txt`            Demo operation sequence
- `docs/`                        `design.md`, `RULES_COMPLIANCE.md`
- `CONTRIBUTIONS.md`             Per-member contribution log

## Setup & Run (from `campus_cache_sim/`)

No external dependencies are required (Python >= 3.11 stdlib only). If using the repo-root `.venv` on Windows:

### 1. Run CLI on the demo sequence
```powershell
..\.venv\Scripts\python.exe -m src.cache_sim.cli demo\sequence.txt
```

### 2. Launch the Interactive Web UI
```powershell
..\.venv\Scripts\python.exe -m src.cache_sim.ui
```
Opens `http://127.0.0.1:8000/` in your browser. Optional flags: `--host`, `--port`, `--capacity`, `--no-browser`.

### 3. Run the Test Suite
```powershell
..\.venv\Scripts\python.exe -m unittest discover -s tests -t . -v
```

*(If your virtual environment is already activated, replace `..\.venv\Scripts\python.exe` with `python`.)*

## Web UI Features
- **Live Frequency Buckets**: Visualizes each frequency's `DoublyLinkedList` ordered **LRU -> MRU**, highlighting `min_freq` and the next eviction victim.
- **Interactive Controls**: `CAPACITY`, `PUT`, `GET` (or click any cached card to `GET`), `STATE`, `ANALYTICS`, and `Reset`.
- **Script Player**: Preloaded with `demo/sequence.txt`, supporting **Step Next**, **Auto-Play / Pause**, **Run All**, and **Rewind**.
- **Analytics & Internals**: Live hits/misses, hit ratio, per-frequency eviction breakdown, longest-lived victim, `HashMap` bucket/load-factor stats, and operation log.

## Input Format
```text
CAPACITY 2
PUT A 10
GET A
STATE
RESIZE 3        # extension
ANALYTICS       # extension
```

## Extensions Status
- **Implemented**: `Analytics` (`analytics.py`), interactive Web UI (`ui.py`, `static/index.html`), reference cache & stress tests (`reference_cache.py`, `test_reference_cache.py`, `test_stress.py`).
- **Pending (`TODO`)**: Live `RESIZE` in `LFUCache` (`cache.py`).

# tracked-mapping

Dict and list wrappers that track key access for reporting unconsumed data.

Wrap a parsed JSON/YAML/TOML structure in `TrackedDict`, read what you need
through normal dict access, then call `unaccessed()` to get dotted paths for
every key that was never touched.

## Install

```bash
pip install tracked-mapping
```

## Usage

```python
import json
from tracked_mapping import TrackedDict

with open("config.json") as f:
    data = TrackedDict(json.load(f))

name = data["project"]["name"]
version = data["project"]["version"]

for path in data.unaccessed():
    print(f"  unhandled: {path}")
```

## API

### `TrackedDict(data: dict, _path: str = "")`

- `d[key]` / `d.get(key, default)` — read access; marks `key` as accessed
- `key in d`, `len(d)`, `bool(d)`, `iter(d)` — standard container ops (do **not** mark accessed)
- `d.keys()` — returns keys (does **not** mark accessed)
- `d.values()` / `d.items()` — iterate with wrapping; marks all keys accessed
- `d.raw` — the underlying plain `dict`
- `d.mark_accessed(*keys)` — explicitly mark keys
- `d.mark_all_accessed()` — mark every key at this level
- `d.unaccessed()` — sorted list of dotted paths for all unaccessed keys, recursively
- `d.accessed_keys()` — set of keys accessed at this level

Nested dicts are automatically wrapped in `TrackedDict`, nested lists in `TrackedList`.

### `TrackedList(data: list, _path: str = "")`

- `lst[i]`, `len(lst)`, `bool(lst)`, `iter(lst)` — standard access
- `lst.raw` — the underlying plain `list`
- `lst.unaccessed()` — collects unaccessed paths from wrapped children

## How it works

When you access a key via `[]` or `.get()`, `TrackedDict` records that key.
Nested dicts and lists are lazily wrapped on first access so their keys are
tracked too. After your parser finishes, `unaccessed()` walks the tree and
returns dotted paths (e.g. `"server.timeout"`, `"users[0].email"`) for
anything never read.

This catches both parser omissions (data present but ignored) and unknown
user-supplied fields — without maintaining a separate list of expected keys.

## License

MIT

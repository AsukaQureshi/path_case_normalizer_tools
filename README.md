# path_case_normalizer_tools

Normalizes path casing so you can detect when two paths that look different would collide on a case-insensitive filesystem (macOS, Windows).

```python
from path_case_normalizer_tools import normalize_path, paths_are_conflicting, find_conflicts

normalize_path("Foo/Bar.txt")          # -> "foo/bar.txt"
paths_are_conflicting("Foo/Bar.txt", "foo/bar.txt")  # -> True
find_conflicts(["Foo.txt", "foo.txt", "bar.txt"])   # -> [[0, 1]]
```

The problem this exists for: a build system or asset manifest generated on Linux can contain `Assets/Header.png` and `assets/header.png` as two separate files. Copy that tree onto an APFS or NTFS volume and one silently clobbers the other. This library compares paths as pure strings — it never touches the filesystem — so it catches the collision before it happens.

The trade-off: because it is string-only, two paths that point at different inodes on a case-sensitive system but would collide case-insensitively are still reported as conflicts. That is the behaviour you want for pre-flight checks; it is not what you want if you are trying to reason about a Linux filesystem.

The awkward edge: Unicode. `str.lower()` does not consider the German `Straße` and `STRASSE` equivalent, but a case-insensitive filesystem does. `normalize_path` accepts a `case` argument — `"lower"` (default) or `"fold"` (uses `str.casefold`, which is closer to what real case-insensitive filesystems do). Pick the one that matches the filesystem you are targeting and pass it consistently. The same pair of paths can be a conflict under `"fold"` and not under `"lower"`.

Separator handling is explicit, not platform-detected. Pass `sep="/"` for POSIX paths and `sep="\\"` for Windows paths. Multi-character separators (e.g. `"::"`) are supported. Leading, trailing, and consecutive separators are preserved so that `normalize_path("A/B/") == "a/b/"`, which `str.split`-based implementations get wrong.

`None` is rejected with `TypeError`; it is not silently coerced to the string `"None"`.

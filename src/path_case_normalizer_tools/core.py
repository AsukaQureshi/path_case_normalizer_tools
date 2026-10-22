"""Core normalization and conflict-detection logic.

Design decisions (documented once here, referenced from functions):

1. Pure-string comparison. We never touch the filesystem, so two paths that
   point at different inodes on a case-sensitive system but would collide on
   macOS/Windows are still treated as conflicts. That is the whole point — the
   library exists to catch conflicts *before* they become a problem on a
   case-insensitive filesystem.

2. Unicode case folding via str.casefold(), by default. Comparing with .lower()
   fails on non-ASCII pairs like the German "Straße" / "STRASSE" that should be
   treated as equivalent on a case-insensitive filesystem. .casefold() is the
   closest pure-Python analogue to what real case-insensitive filesystems do.
   The caller can choose "lower" if they prefer classic .lower() semantics.

3. Component-wise separators. Some paths embed separators that should be
   treated as ordinary characters inside a component (e.g. spaces). Rather than
   guess at that, we split on the given ``sep`` and fold each component
   independently, preserving the separator in the output. This keeps round-
   tripping trivial: normalize_path(p) uses the same separator count as p.

4. ``None`` is not a path. Passing None raises TypeError rather than being
   coerced to the string "None", because quiet coercion of None into a real
   path string is a classic source of false positives.
"""

from __future__ import annotations


def normalize_path(path, sep="/", case="lower"):
    """Return *path* with every component case-normalized.

    Splitting on ``sep`` (rather than os.sep) keeps this function deterministic
    and platform-independent: a Windows-style path "a\\B\\c" passed with
    sep="\\" folds each component the same way as a POSIX "a/b/c".

    The empty string maps to the empty string; a bare separator maps to itself;
    a leading or trailing separator is preserved.

    Args:
        path: a str. ``None`` raises TypeError — see design note 4 in the
            module docstring.
        sep: the component separator to split and rejoin on. Must be a str.
        case: "lower" (uses str.lower) or "fold" (uses str.casefold). See
            design note 2 for why casefold is the default semantics.

    Returns:
        str: the normalized path.

    Raises:
        TypeError: path is None, or path/sep/case is not a str.
        ValueError: case is not one of {"lower", "fold"}.
    """
    if path is None:
        raise TypeError("path must be a str, not None")
    if not isinstance(path, str):
        raise TypeError(f"path must be a str, not {type(path).__name__}")
    if not isinstance(sep, str):
        raise TypeError(f"sep must be a str, not {type(sep).__name__}")
    if not isinstance(case, str):
        raise TypeError(f"case must be a str, not {type(case).__name__}")
    if case == "lower":
        fold = str.lower
    elif case == "fold":
        fold = str.casefold
    else:
        raise ValueError(f"case must be 'lower' or 'fold', not {case!r}")

    # str.split preserves leading empty components but DROPS trailing empties,
    # which would corrupt round-tripping for paths like "a/b/". The manual
    # walk below preserves every separator exactly.
    if path == "":
        return ""

    out_chars = []
    component = []
    sep_len = len(sep)
    i = 0
    n = len(path)
    while i < n:
        if sep and path[i : i + sep_len] == sep:
            out_chars.append(fold("".join(component)))
            out_chars.append(sep)
            component = []
            i += sep_len
        else:
            component.append(path[i])
            i += 1
    out_chars.append(fold("".join(component)))
    return "".join(out_chars)


def paths_are_conflicting(a, b, sep="/", case="lower"):
    """True if *a* and *b* differ only in case after component-wise folding.

    Two paths conflict when they are not byte-for-byte identical but their
    case-normalized forms are equal. On a case-insensitive filesystem such
    paths would refer to the same file.

    Raises the same errors as normalize_path on bad inputs.
    """
    if a == b:
        return False
    return normalize_path(a, sep=sep, case=case) == normalize_path(b, sep=sep, case=case)


def find_conflicts(paths, sep="/", case="lower"):
    """Group indices of *paths* that conflict pairwise by case only.

    Returns a list of lists, each inner list holding the 0-based indices into
    *paths* that all normalize to the same string but are not all identical.
    Groups are sorted by their first index, and within a group indices are
    ascending. A path that has no case-conflict partner appears in no group.

    The grouping is O(n²) in the worst case; the library is aimed at small path
    sets (build outputs, manifest entries) where clarity beats asymptotic
    cleverness, and where pairwise comparison is easier to reason about than a
    hash-bucket approach that would need to distinguish "identical" from
    "case-conflicting" with extra bookkeeping.
    """
    if not isinstance(paths, list):
        raise TypeError(f"paths must be a list, not {type(paths).__name__}")
    for p in paths:
        if not isinstance(p, str):
            raise TypeError(
                f"each path must be a str, not {type(p).__name__}"
            )

    n = len(paths)
    # clusters[canonical_normal_form] = list of original-path indices
    clusters: dict[str, list[int]] = {}
    # originals[canonical_normal_form] = set of original (un-normalized) paths
    originals: dict[str, set[str]] = {}
    for i, p in enumerate(paths):
        nf = normalize_path(p, sep=sep, case=case)
        clusters.setdefault(nf, []).append(i)
        originals.setdefault(nf, set()).add(p)

    result = []
    for nf in sorted(clusters, key=lambda k: clusters[k][0]):
        indices = clusters[nf]
        if len(indices) < 2:
            continue
        if len(originals[nf]) < 2:
            # All indices point at the exact same string — no case conflict.
            continue
        result.append(sorted(indices))
    return result

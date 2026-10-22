"""path_case_normalizer_tools: normalize path casing for case-insensitive filesystems.

Public API:
    normalize_path(path, sep="/", case="lower") -> str
    paths_are_conflicting(a, b, sep="/", case="lower") -> bool
    find_conflicts(paths, sep="/", case="lower") -> list[list[int]]
"""

from .core import find_conflicts, normalize_path, paths_are_conflicting

__all__ = ["find_conflicts", "normalize_path", "paths_are_conflicting"]

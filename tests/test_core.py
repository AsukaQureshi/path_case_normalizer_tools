"""Unit tests for path_case_normalizer_tools.core.

All tests are deterministic — no wall-clock time, no sleeping, no float ==.
"""

import unittest

from path_case_normalizer_tools.core import (
    find_conflicts,
    normalize_path,
    paths_are_conflicting,
)


class TestNormalizePath(unittest.TestCase):
    def test_lowercases_ascii(self):
        self.assertEqual(normalize_path("Foo/Bar/Baz.txt"), "foo/bar/baz.txt")

    def test_preserves_separator_count(self):
        # Trailing separators must survive — str.split would drop them.
        self.assertEqual(normalize_path("A/B/"), "a/b/")
        self.assertEqual(normalize_path("/A/B"), "/a/b")
        self.assertEqual(normalize_path("/A/B/"), "/a/b/")

    def test_consecutive_separators_preserved(self):
        self.assertEqual(normalize_path("A//B"), "a//b")

    def test_single_separator_only(self):
        self.assertEqual(normalize_path("/"), "/")

    def test_empty_string_round_trips(self):
        self.assertEqual(normalize_path(""), "")

    def test_case_fold_option(self):
        # German sharp-s: lower() keeps it, casefold() maps it to "ss".
        self.assertEqual(normalize_path("Straße", case="fold"), "strasse")
        self.assertEqual(normalize_path("Straße", case="lower"), "straße")

    def test_custom_separator_lowercases_components(self):
        self.assertEqual(normalize_path("A\\B\\C", sep="\\"), "a\\b\\c")

    def test_multichar_separator_supported(self):
        # A multi-character sep must be matched as a whole, not per char.
        self.assertEqual(normalize_path("A::B::C", sep="::"), "a::b::c")

    def test_none_raises_type_error(self):
        with self.assertRaises(TypeError):
            normalize_path(None)

    def test_non_string_path_raises(self):
        with self.assertRaises(TypeError):
            normalize_path(123)

    def test_bad_case_raises_value_error(self):
        with self.assertRaises(ValueError):
            normalize_path("a/b", case="uppercase")

    def test_bad_case_type_raises(self):
        with self.assertRaises(TypeError):
            normalize_path("a/b", case=1)

    def test_non_string_sep_raises(self):
        with self.assertRaises(TypeError):
            normalize_path("a/b", sep=0)


class TestPathsAreConflicting(unittest.TestCase):
    def test_basic_conflict(self):
        self.assertTrue(paths_are_conflicting("Foo/Bar.txt", "foo/bar.txt"))

    def test_identical_paths_not_conflicting(self):
        self.assertFalse(paths_are_conflicting("foo/bar", "foo/bar"))

    def test_different_paths_not_conflicting(self):
        self.assertFalse(paths_are_conflicting("foo/bar", "foo/baz"))

    def test_case_fold_unicode_conflict(self):
        self.assertTrue(paths_are_conflicting("Straße", "STRASSE", case="fold"))
        self.assertFalse(paths_are_conflicting("Straße", "STRASSE", case="lower"))

    def test_custom_separator_conflict(self):
        self.assertTrue(paths_are_conflicting("A\\B", "a\\b", sep="\\"))

    def test_case_sensitive_difference_not_conflict(self):
        # Different basename entirely — not a case conflict.
        self.assertFalse(paths_are_conflicting("foo/bar", "foo/BarX"))


class TestFindConflicts(unittest.TestCase):
    def test_single_conflict_pair(self):
        paths = ["Foo.txt", "foo.txt"]
        self.assertEqual(find_conflicts(paths), [[0, 1]])

    def test_three_way_conflict(self):
        paths = ["Foo.txt", "FOO.txt", "foo.txt"]
        self.assertEqual(find_conflicts(paths), [[0, 1, 2]])

    def test_two_separate_conflict_groups_sorted(self):
        paths = ["A/b", "c/D", "a/B", "C/d"]
        self.assertEqual(find_conflicts(paths), [[0, 2], [1, 3]])

    def test_identical_paths_only_no_conflict(self):
        # Same string repeated is not a case conflict.
        paths = ["foo.txt", "foo.txt", "foo.txt"]
        self.assertEqual(find_conflicts(paths), [])

    def test_mix_of_conflicts_and_clean_paths(self):
        paths = ["Foo.txt", "bar.txt", "foo.txt", "baz.txt"]
        self.assertEqual(find_conflicts(paths), [[0, 2]])

    def test_mix_with_exact_duplicates(self):
        # A duplicate string alongside a genuine case-conflict.
        paths = ["Foo.txt", "foo.txt", "Foo.txt"]
        self.assertEqual(find_conflicts(paths), [[0, 1, 2]])

    def test_empty_list(self):
        self.assertEqual(find_conflicts([]), [])

    def test_single_path(self):
        self.assertEqual(find_conflicts(["anything"]), [])

    def test_no_paths_conflict(self):
        paths = ["a.txt", "b.txt", "c.txt"]
        self.assertEqual(find_conflicts(paths), [])

    def test_custom_separator(self):
        paths = ["A\\B", "a\\b", "C\\D"]
        self.assertEqual(find_conflicts(paths, sep="\\"), [[0, 1]])

    def test_case_fold_semantics(self):
        paths = ["Straße", "STRASSE", "other"]
        self.assertEqual(find_conflicts(paths, case="fold"), [[0, 1]])
        self.assertEqual(find_conflicts(paths, case="lower"), [])

    def test_non_list_paths_raises(self):
        with self.assertRaises(TypeError):
            find_conflicts("not a list")

    def test_non_string_member_raises(self):
        with self.assertRaises(TypeError):
            find_conflicts(["a", 1, "b"])


if __name__ == "__main__":
    unittest.main()

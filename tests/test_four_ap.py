# Copyright (c) 2026 Boon Suan Ho
# SPDX-License-Identifier: MIT

"""Behavioral and mathematical checks for the Python implementation.

The Lean development proves the infinite construction. These tests check the
Python port's public API, finite outputs, and handling of both AP directions.
Run with ``python3 -m unittest discover -s tests -v``.
"""

import itertools
from pathlib import Path
import subprocess
import sys
import unittest

from four_ap import Permutation, extend


PAPER_PREFIX = [0, 1, 3, 2, 11, 7, 15, 9, 5, 6, 4, 2063, 1039, 527, 2575]
ROOT = Path(__file__).resolve().parents[1]


def binary_before(a: int, b: int) -> bool:
    """Independent comparison using the least set bit of the XOR."""
    first_difference = (a ^ b) & -(a ^ b)
    return bool(a & first_difference)


class PermutationTests(unittest.TestCase):
    def test_paper_prefixes(self):
        self.assertEqual(Permutation().prefix(15), PAPER_PREFIX)
        self.assertEqual(
            Permutation(positive=True).prefix(15), [n + 1 for n in PAPER_PREFIX]
        )

    def test_both_inverse_laws(self):
        for positive in (False, True):
            with self.subTest(positive=positive):
                permutation = Permutation(positive=positive)
                values = permutation.prefix(100)
                self.assertEqual(len(set(values)), 100)
                for index, value in enumerate(values):
                    self.assertEqual(permutation.position(value), index)
                    self.assertEqual(permutation.value(permutation.position(value)), value)
                for value in range(int(positive), 9 + int(positive)):
                    index = permutation.position(value)
                    self.assertEqual(permutation.value(index), value)

    def test_inverse_can_find_a_large_value_early(self):
        permutation = Permutation()
        self.assertEqual(permutation.position(2063), 11)
        self.assertEqual(permutation.value(11), 2063)
        self.assertEqual(permutation.prefix(15), PAPER_PREFIX)

    def test_iteration_and_interleaved_queries(self):
        permutation = Permutation()
        iterator = iter(permutation)
        first = [next(iterator) for _ in range(4)]
        self.assertEqual(permutation.position(2063), 11)
        rest = list(itertools.islice(iterator, 11))
        self.assertEqual(first + rest, PAPER_PREFIX)
        self.assertEqual(list(itertools.islice(permutation, 15)), PAPER_PREFIX)

    def test_returned_prefix_is_a_copy(self):
        permutation = Permutation()
        result = permutation.prefix(15)
        result[0] = 999
        result.append(999)
        self.assertEqual(permutation.prefix(15), PAPER_PREFIX)
        self.assertEqual(permutation.prefix(0), [])
        self.assertEqual(permutation.prefix(4), PAPER_PREFIX[:4])

    def test_no_four_term_subsequence_in_either_direction(self):
        word = Permutation().prefix(100)
        positions = {value: index for index, value in enumerate(word)}
        for i, a in enumerate(word):
            for j in range(i + 1, len(word)):
                difference = word[j] - a  # May be positive or negative.
                k = positions.get(a + 2 * difference, -1)
                l = positions.get(a + 3 * difference, -1)
                self.assertFalse(j < k < l, (a, difference, (i, j, k, l)))

    def test_natural_argument_validation(self):
        permutation = Permutation()
        for method in (permutation.value, permutation.position, permutation.prefix):
            with self.subTest(method=method.__name__):
                with self.assertRaises(ValueError):
                    method(-1)
                for invalid in (True, False, 1.5, "3", None):
                    with self.subTest(invalid=invalid), self.assertRaises(TypeError):
                        method(invalid)
        with self.assertRaises(TypeError):
            Permutation(positive=1)
        with self.assertRaises(ValueError):
            Permutation(positive=True).position(0)
        self.assertEqual(permutation.prefix(15), PAPER_PREFIX)


class ExtensionTests(unittest.TestCase):
    def test_base_case_is_the_reverse_binary_listing(self):
        self.assertEqual(extend([], range(8)), [0, 4, 2, 6, 1, 5, 3, 7])
        self.assertEqual(extend([0], range(8)), extend([], range(8)))
        self.assertEqual(extend([], []), [])
        self.assertEqual(extend([0], []), [0])

    def test_preserves_inputs_and_accepts_iterables(self):
        word = [0, 1, 3, 2]
        targets = {4, 6}
        old_word, old_targets = word.copy(), targets.copy()
        result = extend(word, targets)
        self.assertEqual(word, old_word)
        self.assertEqual(targets, old_targets)
        self.assertIsNot(result, word)
        self.assertEqual(result[: len(word)], word)
        self.assertTrue(targets <= set(result))
        self.assertEqual(len(result), len(set(result)))
        self.assertEqual(result, extend(iter(word), (n for n in [4, 6, 4])))

    def test_already_covered_targets_do_not_move_entries(self):
        word = []
        for n in range(9):
            word = extend(word, {n})
            self.assertEqual(extend(word, set(word)), word)
            self.assertEqual(extend(word, []), word)

    def test_small_completions(self):
        # Check C(P), including its infinite binary-ordered tail restricted to
        # a finite range. This checks more than AP-freeness inside P alone.
        base = extend([], range(6))  # Safe by Lemma 1.
        for targets in (set(), {6}, {0, 7}, {2, 8}):
            word = extend(base, targets)
            positions = {value: index for index, value in enumerate(word)}

            def before(a, b):
                ia = positions.get(a, len(word))
                ib = positions.get(b, len(word))
                return ia < ib or (
                    ia == ib == len(word) and binary_before(a, b)
                )

            for a in range(24):
                for b in range(24):
                    if a == b:
                        continue
                    c, d = 2 * b - a, 3 * b - 2 * a
                    if not (0 <= c < 24 and 0 <= d < 24):
                        continue
                    self.assertFalse(
                        before(a, b) and before(b, c) and before(c, d),
                        (targets, (a, b, c, d)),
                    )

    def test_invalid_words_and_targets(self):
        for word in ([0, 0], [1, 1]):
            with self.assertRaises(ValueError):
                extend(word, [])
        for word, targets, error in (
            ([-1], [], ValueError), ([], [-1], ValueError),
            ([True], [], TypeError), ([], [False], TypeError),
            ([1.0], [], TypeError), ([], ["2"], TypeError),
        ):
            with self.subTest(word=word, targets=targets), self.assertRaises(error):
                extend(word, targets)


class CommandLineTests(unittest.TestCase):
    def run_cli(self, *arguments):
        return subprocess.run(
            [sys.executable, str(ROOT / "four_ap.py"), *arguments],
            capture_output=True, text=True, timeout=15, check=False,
        )

    def test_queries(self):
        for arguments, expected in (
            ([], str(PAPER_PREFIX)),
            (["--count", "0"], "[]"),
            (["--index", "11"], "2063"),
            (["--inverse", "2063"], "11"),
            (["--positive", "--index", "11"], "2064"),
            (["--positive", "--inverse", "2064"], "11"),
        ):
            with self.subTest(arguments=arguments):
                result = self.run_cli(*arguments)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(), expected)
                self.assertEqual(result.stderr, "")

    def test_invalid_queries(self):
        for arguments in (
            ["--count", "-1"], ["--index", "1.5"],
            ["--positive", "--inverse", "0"],
            ["--count", "2", "--index", "1"],
        ):
            with self.subTest(arguments=arguments):
                result = self.run_cli(*arguments)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertIn("error:", result.stderr)


if __name__ == "__main__":
    unittest.main()

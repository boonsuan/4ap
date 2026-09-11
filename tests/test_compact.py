# Copyright (c) 2026 Boon Suan Ho
# SPDX-License-Identifier: MIT

"""Regression tests for compact stages, independent of cached query answers."""

from functools import cmp_to_key
import hashlib
import json
import itertools
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from four_ap import Permutation, extend, _BinaryListing


ROOT = Path(__file__).resolve().parents[1]


def reverse_compare(a, b):
    """Independent reference comparison: low bits first, zero before one."""
    if a == b:
        return 0
    bit = (a ^ b) & -(a ^ b)
    return 1 if a & bit else -1


def literal_extend(prefix, targets):
    """Literal implementation of Lemma 2 for small reference cases.

    The guard prevents an accidental huge reference test from exhausting RAM.
    There is deliberately no compact-word code or coverage shortcut here.
    """
    if max(prefix, default=0) == 0:
        return sorted(set(prefix) | targets, key=cmp_to_key(reverse_compare))
    even_prefix = [n // 2 for n in prefix if n % 2 == 0]
    odd_prefix = [n // 2 for n in prefix if n % 2 == 1]
    even_targets = {n // 2 for n in targets if n % 2 == 0}
    even_extension = literal_extend(even_prefix, even_targets)
    new_evens = [2 * n for n in even_extension[len(even_prefix):]]
    h = max(new_evens, default=0)
    if h > 100_000:
        raise AssertionError("Reference test would expand an oversized interval")
    odd_targets = {n // 2 for n in targets if n % 2 == 1} | set(range(h))
    odd_extension = literal_extend(odd_prefix, odd_targets)
    new_odds = [2 * n + 1 for n in odd_extension[len(odd_prefix):]]
    return prefix + new_odds + new_evens


def bounded_range(*args):
    """Catch accidental eager expansion before it can exhaust test-runner RAM."""
    result = range(*args)
    if result.stop - result.start > 100_000:
        raise AssertionError("Permutation queries must not enumerate whole stages")
    return result


class BinaryListingTests(unittest.TestCase):
    def test_interval_boundaries_and_sparse_extras(self):
        for stop in (0, 1, 2, 3, 7, 8, 9, 15, 16, 17):
            for start in range(stop + 1):
                for extras in ((), (stop,), (stop, stop + 3, stop + 16)):
                    with self.subTest(start=start, stop=stop, extras=extras):
                        word = _BinaryListing(start, stop, extras)
                        expected = sorted(
                            list(range(start, stop)) + list(extras),
                            key=cmp_to_key(reverse_compare),
                        )
                        self.assertEqual(word.length, len(expected))
                        self.assertEqual(word.maximum, max(expected, default=-1))
                        self.assertEqual(
                            [word.value(i) for i in range(word.length)], expected
                        )
                        positions = {n: i for i, n in enumerate(expected)}
                        for n in range(-1, stop + 18):
                            self.assertEqual(word.position(n), positions.get(n))
                            self.assertEqual(
                                word.count_below(n), sum(x < n for x in expected)
                            )
                        for parity, child in enumerate(word.parities):
                            self.assertEqual(
                                [child.value(i) for i in range(child.length)],
                                [n // 2 for n in expected if n % 2 == parity],
                            )


class CompactExtensionTests(unittest.TestCase):
    def test_512_small_extensions_against_literal_recursion(self):
        target_sets = (set(), {0}, {1}, {2}, {5}, {8}, {0, 2, 5}, {2, 6, 9})
        count = 0
        for size in range(4):
            for subset in itertools.combinations(range(7), size):
                prefix = sorted(subset, key=cmp_to_key(reverse_compare))
                for targets in target_sets:
                    with self.subTest(prefix=prefix, targets=targets):
                        self.assertEqual(extend(prefix, targets), literal_extend(prefix, targets))
                    count += 1
        self.assertEqual(count, 512)

    def test_compact_stages_against_literal_recursion(self):
        permutation = Permutation()
        expected = []
        for target in range(16):
            expected = literal_extend(expected, {target})
            permutation._advance()
            word = permutation._word
            self.assertEqual(word.length, len(expected))
            self.assertEqual(word.maximum, max(expected, default=-1))
            self.assertEqual([word.value(i) for i in range(word.length)], expected)
            for i, value in enumerate(expected):
                self.assertEqual(word.position(value), i)
            for bound in (0, 1, 2, 8, 16, 100, 2624):
                self.assertEqual(word.count_below(bound), sum(n < bound for n in expected))
        self.assertEqual(len(expected), 354)


class ExtensionSizeGuardTests(unittest.TestCase):
    def test_limit_counts_the_old_prefix_and_is_inclusive(self):
        prefix, targets = [0, 1], {4}
        expected = literal_extend(prefix, targets)
        self.assertEqual(len(expected), 6)
        self.assertEqual(extend(prefix, targets, max_length=6), expected)
        with self.assertRaisesRegex(OverflowError, "6 output entries"):
            extend(prefix, targets, max_length=5)
        self.assertEqual(prefix, [0, 1])
        self.assertEqual(targets, {4})
        # The limit also applies when all targets are already in the prefix.
        with self.assertRaises(OverflowError):
            extend(prefix, [], max_length=1)

    def test_empty_result_and_zero_limit(self):
        self.assertEqual(extend([], [], max_length=0), [])
        with self.assertRaises(OverflowError):
            extend([], [0], max_length=0)

    def test_duplicates_and_iterables_do_not_inflate_the_size(self):
        self.assertEqual(extend(iter([0, 1]), iter([0, 1, 1]), max_length=2), [0, 1])

    def test_explicit_opt_out_and_larger_limit(self):
        expected = literal_extend([0, 1], {4})
        self.assertEqual(extend([0, 1], {4}, max_length=None), expected)
        self.assertEqual(extend([0, 1], {4}, max_length=1000), expected)

    def test_invalid_limits(self):
        with self.assertRaises(ValueError):
            extend([], [], max_length=-1)
        for invalid in (True, False, 1.5, "10"):
            with self.subTest(invalid=invalid), self.assertRaises(TypeError):
                extend([], [], max_length=invalid)
        with self.assertRaises(TypeError):
            extend([], [], 10)  # The limit must be explicitly named.

    def test_input_lower_bound_rejects_before_building_a_plan(self):
        with patch("four_ap._extend_suffix", side_effect=AssertionError("built a plan")):
            with self.assertRaisesRegex(OverflowError, "max_length=2"):
                extend([0], [1, 2], max_length=2)

    def test_stops_reading_an_oversized_prefix(self):
        def oversized_prefix():
            yield from (0, 1, 2)
            raise AssertionError("read past the first over-limit input")

        with self.assertRaisesRegex(OverflowError, "max_length=2"):
            extend(oversized_prefix(), [], max_length=2)

    def test_stops_reading_oversized_targets(self):
        def oversized_targets():
            yield from (0, 1, 1, 2)  # Repeats and existing entries do not count twice.
            raise AssertionError("read past the first over-limit input")

        with self.assertRaisesRegex(OverflowError, "max_length=2"):
            extend([0], oversized_targets(), max_length=2)

    def test_large_range_input_is_not_materialized(self):
        # range can describe more entries than a Python list can hold.
        with self.assertRaisesRegex(OverflowError, "max_length=10"):
            extend([], range(10**100), max_length=10)

    def test_default_rejects_large_output_before_enumerating(self):
        # For P=[0,1] and T={2K}, the output has exactly 2K+2 entries.
        # Patching range makes an accidental output loop fail immediately.
        with patch("four_ap.range", side_effect=AssertionError("enumerated output"),
                   create=True):
            with self.assertRaisesRegex(OverflowError, "max_length=100,000"):
                extend([0, 1], {10**8})

    def test_machine_limit_cannot_be_disabled(self):
        with patch("four_ap.range", side_effect=AssertionError("enumerated output"),
                   create=True):
            # This integer also exceeds Python's usual decimal-formatting cap.
            # The failure message must not try to print thousands of digits.
            for limit in (100_000, None, 1 << 16000):
                with self.subTest(unlimited=limit is None):
                    with self.assertRaisesRegex(OverflowError, "maximum list length"):
                        extend([0, 1], {1 << 15000}, max_length=limit)

    def test_canonical_explosion_is_blocked_before_enumerating(self):
        prefix = Permutation().prefix(354)
        with patch("four_ap.range", side_effect=AssertionError("enumerated output"),
                   create=True):
            with self.assertRaisesRegex(OverflowError, "maximum list length"):
                extend(prefix, {16})


class LargeQueryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.permutation = Permutation()
        with patch("four_ap.range", bounded_range, create=True):
            cls.values = cls.permutation.prefix(1000)

    def test_first_thousand_is_compact_and_distinct(self):
        self.assertEqual(len(self.values), 1000)
        self.assertEqual(len(set(self.values)), 1000)
        # Stored digest for regression checks of the complete 1,000-term prefix.
        encoded = json.dumps(self.values, separators=(",", ":")).encode()
        self.assertEqual(hashlib.sha256(encoded).hexdigest(),
                         "3241a1ac527480289ff6c3fd7deb7250cfd3614a099b89ce248a2b5f775b3c7d")
        self.assertGreater(self.permutation._word.length, 10**100)
        self.assertEqual(len(self.permutation._values), 1000)
        self.assertEqual(self.permutation._next_target, 17)
        # Regression fixture for the first entry after the initial 354 terms.
        self.assertEqual(self.values[354], int(
            "733919557116822883715462686496667821054900796533849959596028428603815320"
            "34831513858240593699524021969750015"
        ))

    def test_fresh_inverse_without_forward_cache(self):
        for index in (0, 10, 353, 354, 355, 700, 999):
            for positive in (False, True):
                with self.subTest(index=index, positive=positive):
                    p = Permutation(positive=positive)
                    value = self.values[index] + int(positive)
                    self.assertEqual(p.position(value), index)
                    self.assertEqual(p.value(index), value)
                    self.assertEqual(len(p._values), 1)

    def test_random_access_beyond_machine_sized_indices(self):
        for index in (10**30, 10**60, 10**100):
            with self.subTest(index=index):
                p = Permutation()
                value = p.value(index)
                self.assertEqual(Permutation().position(value), index)
                self.assertEqual(len(p._values), 1)
                self.assertEqual(p._next_target, 17)

    def test_huge_stage_boundaries_without_materialization(self):
        p = Permutation()
        p.value(354)
        final_index = p._word.length - 1
        value = p.value(final_index)
        self.assertEqual(Permutation().position(value), final_index)
        self.assertEqual(value, 16)
        self.assertEqual(len(p._values), 2)

    def test_interleaved_iteration_and_prefix_copies(self):
        p = Permutation(positive=True)
        iterator = iter(p)
        first = list(itertools.islice(iterator, 354))
        self.assertEqual(p.position(self.values[999] + 1), 999)
        rest = list(itertools.islice(iterator, 646))
        expected = [n + 1 for n in self.values]
        self.assertEqual(first + rest, expected)
        copied = p.prefix(1000)
        copied[0] = -1
        self.assertEqual(p.prefix(1000), expected)
        self.assertEqual(p.prefix(0), [])
        self.assertEqual(p.prefix(3), expected[:3])

    def test_no_four_term_subsequence_in_either_direction(self):
        positions = {value: i for i, value in enumerate(self.values)}
        for i, a in enumerate(self.values):
            for j in range(i + 1, len(self.values)):
                difference = self.values[j] - a
                k = positions.get(a + 2 * difference, -1)
                l = positions.get(a + 3 * difference, -1)
                self.assertFalse(j < k < l, (a, difference, (i, j, k, l)))

    def test_cli_first_thousand_and_large_queries(self):
        for arguments, expected in (
            (["--count", "1000"], str(self.values)),
            (["--index", "999"], str(self.values[999])),
            (["--inverse", str(self.values[999])], "999"),
            (["--positive", "--inverse", str(self.values[999] + 1)], "999"),
        ):
            with self.subTest(arguments=arguments):
                result = subprocess.run(
                    [sys.executable, str(ROOT / "four_ap.py"), *arguments],
                    capture_output=True, text=True, timeout=15, check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(), expected)
                self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()

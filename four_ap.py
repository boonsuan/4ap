#!/usr/bin/env python3
# Copyright (c) 2026 Boon Suan Ho
# SPDX-License-Identifier: MIT

"""Compute the permutation in "A 4AP-free permutation of the positive integers".

This standard-library implementation follows ``FourAP/Extension.lean`` and
``FourAP/Construction.lean``. The Lean development proves the construction;
the tests compare the Python implementation with its finite stages.

The default permutation has nonnegative values and zero-based positions::

    >>> permutation = Permutation()
    >>> permutation.prefix(11)
    [0, 1, 3, 2, 11, 7, 15, 9, 5, 6, 4]
    >>> permutation.value(4)
    11
    >>> permutation.position(11)
    4

``Permutation(positive=True)`` adds one to every value, not to positions.
Stages are stored as compact words, not lists of all their entries. A query
constructs only the stages it needs and reads the relevant branches. Repeated
queries share the stage descriptions and cached forward/inverse answers.

Reading guide: the private word classes below describe finite sequences and
provide indexed lookup, inverse lookup, and normalized parity subsequences.
``_extend_suffix`` then implements the Extension Lemma using those operations.
The public API (``extend`` and ``Permutation``) and command-line entry point
are at the end of the file. See PERFORMANCE.md for a worked explanation.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Iterable, Iterator
from functools import cached_property


# A conservative default for the explicit-list API, not for compact queries.
_DEFAULT_MAX_LENGTH = 100_000


def _natural(value: int, name: str) -> int:
    """Validate a public natural-number argument, excluding booleans."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
    if value < 0:
        raise ValueError(f"{name} must be nonnegative")
    return value


class _Word:
    """A finite word of distinct nonnegative integers, possibly enormous.

    ``length`` is a Python integer, not __len__: stages can exceed sys.maxsize.
    ``maximum`` is -1 for the empty word. ``parities`` contains the normalized
    even and odd subsequences, in that order. Internal value indices are valid;
    position returns None when the value is absent.
    """

    length: int
    maximum: int

    def value(self, index: int) -> int:
        raise NotImplementedError

    def position(self, value: int) -> int | None:
        raise NotImplementedError

    @cached_property
    def parities(self) -> tuple[_Word, _Word]:
        raise NotImplementedError

    def count_below(self, bound: int) -> int:
        """Count entries less than bound without enumerating them."""
        if bound <= 0:
            return 0
        if bound > self.maximum:
            return self.length
        return self._count_below(bound)

    def _count_below(self, bound: int) -> int:
        raise NotImplementedError


class _Explicit(_Word):
    """The caller's finite list, used only by the public extend function."""

    def __init__(self, values: Iterable[int]) -> None:
        self.values = tuple(values)
        self.length = len(self.values)
        self.maximum = max(self.values, default=-1)
        self.positions = {value: i for i, value in enumerate(self.values)}

    def value(self, index: int) -> int:
        return self.values[index]

    def position(self, value: int) -> int | None:
        return self.positions.get(value)

    @cached_property
    def parities(self) -> tuple[_Word, _Word]:
        return (
            _Explicit(n // 2 for n in self.values if n % 2 == 0),
            _Explicit(n // 2 for n in self.values if n % 2 == 1),
        )

    def _count_below(self, bound: int) -> int:
        return sum(n < bound for n in self.values)


class _BinaryListing(_Word):
    """[start, stop) plus distinct extras >= stop, in reverse binary order.

    In this order the even entries come first, then the odd entries. Both
    halves have the same order after division by two. Counting the halves
    gives indexed access and inverse lookup without sorting or expanding an
    interval. start may be 1 to exclude the old prefix entry zero.
    """

    def __init__(self, start: int, stop: int, extras: tuple[int, ...] = ()) -> None:
        self.start, self.stop, self.extras = start, stop, extras
        self.length = stop - start + len(extras)
        self.maximum = max(stop - 1 if stop > start else -1, max(extras, default=-1))

    def value(self, index: int) -> int:
        start, stop, extras = self.start, self.stop, self.extras
        # result holds the low bits already chosen; place is the next power
        # of two. The remaining candidates are quotients after removing them.
        result, place = 0, 1
        while stop - start + len(extras) > 1:
            # There are ceil(stop/2) - ceil(start/2) evens in [start, stop).
            even_count = (stop + 1) // 2 - (start + 1) // 2
            if extras:
                even_count += sum(n % 2 == 0 for n in extras)
            # The base listing is EVEN-first, unlike the appended O E block.
            parity = int(index >= even_count)
            if parity:
                index -= even_count
                result += place
            start = (start + 1 - parity) // 2
            stop = (stop + 1 - parity) // 2
            if extras:
                extras = tuple(n // 2 for n in extras if n % 2 == parity)
            place *= 2
        remaining = start if stop > start else extras[0]
        return result + place * remaining

    def position(self, value: int) -> int | None:
        if not (self.start <= value < self.stop or value in self.extras):
            return None
        start, stop, extras = self.start, self.stop, self.extras
        index = 0
        # An odd value follows every even candidate. Once its quotient is
        # zero it is first in the remaining listing, so there is no more rank
        # to add. This also avoids walking over unused high zero bits.
        while value:
            parity = value % 2
            if parity:
                index += (stop + 1) // 2 - (start + 1) // 2
                if extras:
                    index += sum(n % 2 == 0 for n in extras)
            start = (start + 1 - parity) // 2
            stop = (stop + 1 - parity) // 2
            if extras:
                extras = tuple(n // 2 for n in extras if n % 2 == parity)
            value //= 2
        return index

    @cached_property
    def parities(self) -> tuple[_Word, _Word]:
        return (
            _BinaryListing(
                (self.start + 1) // 2, (self.stop + 1) // 2,
                tuple(n // 2 for n in self.extras if n % 2 == 0),
            ),
            _BinaryListing(
                self.start // 2, self.stop // 2,
                tuple(n // 2 for n in self.extras if n % 2 == 1),
            ),
        )

    def _count_below(self, bound: int) -> int:
        return max(0, min(bound, self.stop) - self.start) + sum(
            n < bound for n in self.extras
        )


_EMPTY = _BinaryListing(0, 0)


class _Concat(_Word):
    """The first word followed by the second; their entries are disjoint."""

    def __init__(self, first: _Word, second: _Word) -> None:
        self.first, self.second = first, second
        self.length = first.length + second.length
        self.maximum = max(first.maximum, second.maximum)

    def value(self, index: int) -> int:
        if index < self.first.length:
            return self.first.value(index)
        return self.second.value(index - self.first.length)

    def position(self, value: int) -> int | None:
        index = self.first.position(value)
        if index is not None:
            return index
        index = self.second.position(value)
        return None if index is None else self.first.length + index

    @cached_property
    def parities(self) -> tuple[_Word, _Word]:
        first_even, first_odd = self.first.parities
        second_even, second_odd = self.second.parities
        return _concat(first_even, second_even), _concat(first_odd, second_odd)

    def _count_below(self, bound: int) -> int:
        return self.first.count_below(bound) + self.second.count_below(bound)


def _concat(first: _Word, second: _Word) -> _Word:
    if not first.length:
        return second
    if not second.length:
        return first
    return _Concat(first, second)


class _OddEven(_Word):
    """The new suffix O E: (2x+1 for x in odd), then (2x for x in even)."""

    def __init__(self, odd: _Word, even: _Word) -> None:
        self.odd, self.even = odd, even
        self.length = odd.length + even.length
        self.maximum = max(2 * odd.maximum + 1, 2 * even.maximum)

    def value(self, index: int) -> int:
        if index < self.odd.length:
            return 2 * self.odd.value(index) + 1
        return 2 * self.even.value(index - self.odd.length)

    def position(self, value: int) -> int | None:
        if value < 0 or value > self.maximum:
            return None
        if value % 2:
            return self.odd.position(value // 2)
        index = self.even.position(value // 2)
        return None if index is None else self.odd.length + index

    @cached_property
    def parities(self) -> tuple[_Word, _Word]:
        return self.even, self.odd

    def _count_below(self, bound: int) -> int:
        return self.even.count_below((bound + 1) // 2) + self.odd.count_below(bound // 2)


class _Targets:
    """The target set [0, limit) union extras, with no interval expansion."""

    def __init__(self, limit: int = 0, extras: Iterable[int] = ()) -> None:
        self.limit = limit
        self.extras = frozenset(n for n in extras if n >= limit)

    def covered_by(self, word: _Word) -> bool:
        # Distinctness is crucial: exactly limit entries below limit means
        # that every integer in [0, limit) occurs. Check sparse extras too.
        return word.count_below(self.limit) == self.limit and all(
            word.position(n) is not None for n in self.extras
        )


def _extend_suffix(prefix: _Word, targets: _Targets) -> _Word:
    """Lemma 2, returning only the new suffix as a compact word.

    The prefix is never expanded, including when extending an already compact
    stage. Its parity subsequences are shared and cached by the word nodes.
    """
    if targets.covered_by(prefix):
        return _EMPTY
    if prefix.maximum <= 0:
        start = int(bool(prefix.length))  # Omit zero if it is already in P.
        stop = max(start, targets.limit)
        extras = tuple(sorted(n for n in targets.extras if n >= start))
        return _BinaryListing(start, stop, extras)

    # First extend the normalized even subsequence. Halving the even targets
    # in [0, limit) produces [0, ceil(limit/2)).
    even_prefix, odd_prefix = prefix.parities
    even_targets = _Targets(
        (targets.limit + 1) // 2, (n // 2 for n in targets.extras if n % 2 == 0)
    )
    even_suffix = _extend_suffix(even_prefix, even_targets)
    h = 2 * even_suffix.maximum if even_suffix.length else 0

    # Force the small odd targets by enlarging an endpoint, NOT set(range(h)).
    # These new odds must precede the new evens, exactly as in the proof.
    odd_targets = _Targets(
        max(targets.limit // 2, h), (n // 2 for n in targets.extras if n % 2 == 1)
    )
    odd_suffix = _extend_suffix(odd_prefix, odd_targets)
    return _OddEven(odd_suffix, even_suffix)


def _check_materialization_size(length: int, max_length: int | None) -> None:
    """Reject a known lower bound on the output size before allocating it."""
    # Check the hard limit first: even an opt-out cannot make Python lists
    # longer than sys.maxsize. Do not format astronomical integers as decimal
    # strings here; that can itself be expensive or exceed Python's digit cap.
    if length > sys.maxsize:
        raise OverflowError(
            "extend() would exceed Python's maximum list length. "
            "Use Permutation().prefix(n) or .value(k) for canonical queries; "
            "max_length=None cannot override this hard limit."
        )
    if max_length is not None and length > max_length:
        raise OverflowError(
            f"extend() needs at least {length:,} output entries, exceeding "
            f"max_length={max_length:,}. Use Permutation().prefix(n) or "
            ".value(k) for canonical queries, or explicitly increase "
            "max_length. Set max_length=None to disable the configurable "
            "limit only when the full list is intentional and affordable."
        )


def extend(
    prefix: Iterable[int],
    targets: Iterable[int],
    *,
    max_length: int | None = _DEFAULT_MAX_LENGTH,
) -> list[int]:
    """Return the extension of ``prefix`` prescribed by Lemma 2.

    ``prefix`` must be a *safe word*: a finite list of distinct nonnegative
    integers whose completion by the binary order is 4AP-free. That mathematical
    precondition is established for every word generated by :class:`Permutation`;
    this function checks the entry types and distinctness, but does not attempt
    to decide safety for an arbitrary user-supplied word.

    ``targets`` may be any iterable of nonnegative integers; repetitions have
    no effect. The result begins with the old prefix and contains the targets
    when the safe-word precondition holds. Neither input is mutated, and the
    result is always a new list. This function uses nonnegative values even
    when working alongside a ``Permutation(positive=True)`` instance.

    This function requests the WHOLE extension as a list. By default it raises
    OverflowError if the result would exceed 100,000 entries (including the
    old prefix). The exact size is computed compactly, before any new output
    entries are enumerated. A lower bound is checked as input values are read.
    Increase the keyword-only ``max_length`` deliberately, or use None to
    disable the configurable limit; Python's maximum list length still applies.
    Invalid limits raise TypeError or ValueError, like the other arguments.

    This is an output-count guard, not a runtime or memory guarantee: consuming
    the finite input iterables and building the compact plan still take work,
    and individual integers can be large. For the canonical permutation prefer
    ``Permutation().prefix(n)`` or ``.value(k)`` instead of expanding a stage.
    """
    if max_length is not None:
        max_length = _natural(max_length, "max_length")
    # Every distinct input value must occur in the result. Enforce this lower
    # bound as inputs are read, so an oversized iterable is not exhausted first.
    word: list[int] = []
    seen: set[int] = set()
    for i, entry in enumerate(prefix):
        value = _natural(entry, f"prefix[{i}]")
        if value in seen:
            raise ValueError("prefix must contain distinct entries")
        _check_materialization_size(len(seen) + 1, max_length)
        seen.add(value)
        word.append(value)

    target_set: set[int] = set()
    for i, entry in enumerate(targets):
        value = _natural(entry, f"targets[{i}]")
        if value not in seen:
            _check_materialization_size(len(seen) + 1, max_length)
            seen.add(value)
        target_set.add(value)
    suffix = _extend_suffix(_Explicit(word), _Targets(extras=target_set))
    _check_materialization_size(len(word) + suffix.length, max_length)
    # word is a fresh local copy; neither caller-owned input is mutated.
    word.extend(suffix.value(i) for i in range(suffix.length))
    return word


class Permutation:
    """The paper's canonical permutation, with cached forward and inverse maps.

    Stages force the singleton targets {0}, {1}, {2}, ... in that exact order.
    A query advances only until its answer is present. The entire stage is
    represented compactly; only requested entries are evaluated and cached.

    Set ``positive=True`` to shift values by one, as in the paper's theorem.
    Positions are always zero-based. Iterating an instance starts at position
    zero and uses the same shared cache as :meth:`value` and :meth:`position`.
    """

    def __init__(self, *, positive: bool = False) -> None:
        if not isinstance(positive, bool):
            raise TypeError("positive must be a bool")
        self._offset = int(positive)
        self._word: _Word = _EMPTY
        self._values: dict[int, int] = {}
        self._positions: dict[int, int] = {}
        self._next_target = 0

    def _advance(self) -> None:
        """Construct exactly the next singleton-target stage of the paper."""
        suffix = _extend_suffix(self._word, _Targets(extras=(self._next_target,)))
        self._word = _concat(self._word, suffix)
        self._next_target += 1

    def value(self, index: int) -> int:
        """Return the value at a zero-based position, without expanding its stage."""
        index = _natural(index, "index")
        if index not in self._values:
            while self._word.length <= index:
                self._advance()
            value = self._word.value(index)
            self._values[index] = value
            self._positions[value] = index
        return self._values[index] + self._offset

    def position(self, value: int) -> int:
        """Return the zero-based position of a value (the inverse permutation).

        Stop when the value first appears, which may happen well before the
        stage explicitly targeting it. For example, 2063 appears at stage 9.
        With ``positive=True``, the argument is a positive, shifted value.
        """
        value = _natural(value, "value")
        if self._offset and value == 0:
            raise ValueError("value must be positive when positive=True")
        unshifted = value - self._offset
        if unshifted not in self._positions:
            index = self._word.position(unshifted)
            while index is None:
                self._advance()
                index = self._word.position(unshifted)
            self._positions[unshifted] = index
            self._values[index] = unshifted
        return self._positions[unshifted]

    def prefix(self, length: int) -> list[int]:
        """Return a new list containing the first ``length`` values."""
        length = _natural(length, "length")
        return [self.value(i) for i in range(length)]

    def __iter__(self) -> Iterator[int]:
        """Yield values from position zero onward, reusing this instance's cache."""
        index = 0
        while True:
            yield self.value(index)
            index += 1


def _cli_natural(text: str) -> int:
    """Parse a nonnegative command-line integer for argparse."""
    try:
        value = int(text)
    except ValueError as error:
        raise argparse.ArgumentTypeError("expected a nonnegative integer") from error
    if value < 0:
        raise argparse.ArgumentTypeError("expected a nonnegative integer")
    return value


def main(argv: list[str] | None = None) -> None:
    """Print a prefix, a value, or an inverse value using the requested convention."""
    parser = argparse.ArgumentParser(
        description="Compute the paper's canonical 4AP-free permutation.",
        epilog="Positions are always zero-based. --positive adds one to values.",
    )
    query = parser.add_mutually_exclusive_group()
    query.add_argument(
        "--count", type=_cli_natural,
        help="print this many initial values (default: 15)",
    )
    query.add_argument(
        "--index", type=_cli_natural,
        help="print the value at this zero-based position",
    )
    query.add_argument(
        "--inverse", type=_cli_natural,
        help="print the zero-based position of this value",
    )
    parser.add_argument(
        "--positive", action="store_true",
        help="use positive values instead of nonnegative values",
    )
    args = parser.parse_args(argv)
    permutation = Permutation(positive=args.positive)

    if args.index is not None:
        print(permutation.value(args.index))
    elif args.inverse is not None:
        if args.positive and args.inverse == 0:
            parser.error("--inverse must be positive when --positive is selected")
        print(permutation.position(args.inverse))
    else:
        print(permutation.prefix(15 if args.count is None else args.count))


if __name__ == "__main__":
    main()

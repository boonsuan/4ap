# Computing with compact stages

The Python implementation describes finite stages of the paper's construction
without listing all their entries. It supports indexed lookup, inverse lookup,
finite prefixes, iteration, and positive values. There are no precomputed
stages or special cases for the first 1,000 terms.

## Querying the permutation

```python
from four_ap import Permutation

p = Permutation()
first_thousand = p.prefix(1000)
term = p.value(999)                 # Positions are always zero-based.
assert p.position(term) == 999
assert Permutation().position(term) == 999  # Works without a forward cache.
```

A fresh `value(999)` query does not evaluate the preceding 999 entries.
`prefix(1000)` returns exactly 1,000 entries, not the rest of the finite stage
that contains them. Returned lists are independent copies.
`Permutation(positive=True)` adds one to values, not to positions.

## Why a compact representation matters

After forcing target 8, the canonical stage has 354 entries. Forcing target 16
produces a stage with about `8.65 * 10**103` entries. Constructing that entire
list just to answer `value(354)` is infeasible.

A compact word records its exact length and maximum as Python integers.
It does not implement `__len__`: that method's result must fit in
`sys.maxsize`, whereas the symbolic length need not. Selected positions can
therefore be larger than machine-sized integers.

## Reading the implementation

Start with `_extend_suffix` for the mathematical construction, then read the
word classes for its data representation, and `Permutation` for the query
interface. `_extend_suffix` implements the Extension Lemma with the existing
prefix factored out: it returns only the appended suffix. It normalizes the
parity words, extends the even part, calculates `h`, extends the odd part,
then puts `O` before `E`. Names and comments distinguish normalized suffixes
from their rescaled values.

`_Targets` describes `[0, limit)` together with a finite set of extras outside
that interval. The normalized even targets have interval endpoint
`(limit + 1) // 2`; the normalized odd targets have endpoint `limit // 2`.
Forcing all values below `h` replaces the latter endpoint by
`max(limit // 2, h)`. No `set(range(h))` is constructed.

The four word forms have separate responsibilities:

| Class | Meaning |
| --- | --- |
| `_Explicit` | A caller-supplied finite word used by `extend` |
| `_BinaryListing` | An interval and sparse extras in reverse binary order |
| `_Concat` | One word followed by another, such as a prefix and its appended suffix |
| `_OddEven` | Normalized odd/even suffixes rescaled and ordered as `O E` |

Every form supplies lookup by index, lookup by value, normalized parity
subsequences, and a count of values below a bound. Descriptions share their
children, and normalized parity words are cached. A compact stage can serve
as the prefix of the next extension without being expanded.

For example, an `_OddEven` node contains `2*x + 1` for each entry of its odd
child, followed by `2*x` for each entry of its even child. If the odd child has
length `a`, index `i < a` is read from that child, and index `i >= a` is read
from the even child at `i-a`. Inverse lookup chooses the child by the value's
parity and adds the odd child's length when appropriate.

The base `_BinaryListing` is different: reverse binary order is **even-first**.
In an interval `[start, stop)`, its even half contains
`ceil(stop/2) - ceil(start/2)` entries. This count, plus any even extras, tells
us which half contains an index. Halving the chosen candidates repeats the
same problem one bit higher. The code records the chosen low bits without
sorting or enumerating the interval. Inverse lookup accumulates the sizes of
skipped even halves.

The distinction between the **even-first base listing** and the **odd-first
appended suffix** is essential.

Targets covered by a prefix produce an empty suffix. Coverage of `[0, limit)`
is checked by counting prefix entries below `limit`: since entries are distinct
and nonnegative, a count of `limit` means all those targets are present. Extras
are checked separately. A covered singleton target leaves its stage intact.

## Explicit extensions and the size limit

`extend(prefix, targets, *, max_length=100_000)` returns the **whole** result as
a Python list. The limit counts **all output entries, including the prefix**.
An excessive result raises `OverflowError` rather than attempting to build
that list.

The function validates entries and checks a lower bound as it consumes the
finite input iterables: each distinct input value must occur in the result.
This stops oversized inputs before exhausting them. It then builds a compact
extension plan and checks the exact length **before enumerating any appended
output entries**. Repeated targets do not count twice, and caller-owned
containers are not modified. Iterators are consumed only as far as the call
progresses.

```python
from four_ap import extend

extend([0, 1], {4}, max_length=6)  # Exactly six entries: allowed.
# extend([0, 1], {4}, max_length=5) raises OverflowError.

# Rejects the huge canonical extension without enumerating its output:
# extend(Permutation().prefix(354), {16})

# Explicit limits for deliberately materialized, affordable results:
result = extend([0, 1], {4}, max_length=200_000)
result = extend([0, 1], {4}, max_length=None)
```

`max_length=None` disables the configurable guard. A result longer than
`sys.maxsize` is always rejected, since it cannot be a Python list. Error
messages do not attempt to print astronomical integers with thousands of
digits. Zero is a valid limit and permits only an empty result. Invalid limits
raise `TypeError` or `ValueError`.

This is an **output-count guard**, not a universal time or memory guarantee.
Consuming inputs with many repeated values and building a complicated compact
plan can take substantial work. Individual integers can be large, and disabling
the guard can exhaust memory. Inputs must be finite. For the canonical
permutation, use `Permutation.prefix`, `value`, or `position` rather than
explicitly materializing an extension.

## Measuring performance

```sh
python3 benchmark_four_ap.py --count 1000 --repeat 7
```

Each sample uses a fresh `Permutation` instance. The benchmark excludes
interpreter startup and output formatting. An example run on CPython 3.13.5 /
Linux x86-64 gives these results over seven samples:

| Operation | Median | Observed range |
| --- | ---: | ---: |
| First 1,000 terms | 0.0753 s | 0.0738-0.0779 s |
| 1,000th term only | 0.00176 s | 0.00164-0.00188 s |
| Fresh inverse lookup of that value | 0.00182 s | 0.00171-0.00199 s |

Machine speed and load affect timings. The benchmark is manual rather than a
timing assertion in CI. Python requires 3.10 or later and no third-party
packages.

## Tests and limitations

```sh
python3 -m doctest four_ap.py
python3 -m unittest discover -s tests -v
```

Tests compare 512 small extensions with a literal list/set implementation of
the Extension Lemma, compare complete small stages, and check interval
boundaries and sparse extras. A stored digest of the first 1,000 entries and
a selected value provide regression checks for changes to that prefix.

Tests also cover uncached forward/inverse queries, positive mode, interleaved
iteration, copied prefixes, astronomical indices, huge-stage boundaries, and
absence of 4AP subsequences in both directions among the first 1,000 entries.
Size-guard tests cover inclusive limits, explicit overrides, argument
validation, input preservation, bounded input consumption, and rejection of
astronomical output without entering an output loop.

The Lean integration test compares finite Python outputs with the proved Lean
construction. It requires Lake and a built Lean project; it is skipped when
Lake is absent. Repository CI runs it with the Lean toolchain available. The
Python implementation is tested, not itself formally verified.

Not every index is cheap. More distant compact stages may be expensive to
build. A base-listing query takes parity steps bounded by the bit length of
its values, with extra work for sparse targets at each step. Queries also
traverse word nodes, large-integer arithmetic is not constant time, and
Python's recursion limit matters. Compact queries avoid unrequested output;
they do not provide a general constant-time guarantee.

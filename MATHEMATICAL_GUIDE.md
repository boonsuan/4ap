# A mathematical guide to the formalization

The source follows the proof of the paper *A 4AP-free permutation of the
positive integers*. This guide explains the small changes of language needed
for Lean and suggests a reading order. It supplements the paper; it does not
replace any proof with an informal argument.

## 1. What the final theorem says

Start at `FourAP/Main.lean`, whose last declaration is the theorem with positive
indices and positive values. An equivalence `f : ℕ+ ≃ ℕ+` includes a function,
an inverse, and proofs that the two functions are mutually inverse. Four
indices `i < j < k < l` cannot carry the four values `a, a+r, a+2r, a+3r` when
`r : ℤ` is nonzero.

The construction itself uses nonnegative values. Its unshifted version is a
bijection `ℕ ≃ ℕ`. The notation `SequenceAPFree` says that four values at
increasing positions never satisfy `IsAP4`.

## 2. Arithmetic progressions without truncated subtraction

In `FourAP/Basic.lean`, the proposition `IsAP4 a b c d` is the conjunction

\[
a\ne b,\qquad a+c=2b,\qquad b+d=2c.
\]

All four variables here are natural numbers. This formulation treats increasing
and decreasing progressions uniformly. In particular, it avoids using `b-a`
in natural-number arithmetic, where subtraction is truncated at zero.

`isAP4_iff_integer_progression` proves that this is equivalent to the existence
of an integer `r ≠ 0` with `b=a+r`, `c=a+2r`, and `d=a+3r`. There is therefore no
change of mathematical meaning hidden in the choice of equations.

For a strict relation `R`, `APFree R` means that no such quadruple satisfies
`R a b`, `R b c`, and `R c d`.

## 3. The binary order

Read `FourAP/Binary.lean` next. `binaryCompare` examines the lowest bits first.
When the bits agree it recurses on the quotients by two; when they differ, the
number whose bit is one precedes the number whose bit is zero. Both arguments
zero is the stopping case.

`bits a b` means that this Boolean comparison returns true. The theorem
`bits_iff_first_differing_bit` identifies it with the paper's literal definition:
there is a bit position at which `a` has one and `b` has zero, and all smaller
bit positions agree. `bits_irrefl`, `bits_asymm`, `bits_trans`, and `bits_total`
verify that this is a strict linear order.

The arithmetic arguments are the paper's bit argument written recursively.
Equal low bits are removed; otherwise parity decides the comparison. This
proves both 3AP-freeness and equation (1). No results from the cited papers
are assumed.

The ordinary numerical comparisons `≤` and `<` on naturals retain their usual
meaning throughout. The binary comparison is always written `bits`, so an
inequality such as `y ≤ 2*x` cannot be confused with binary order.

## 4. Finite words and their completions

Words are `List ℕ`. `List.Nodup` expresses that their entries are distinct.
`P.IsPrefix Q` means that there exists a suffix `S` with `P ++ S = Q`; thus a
prefix is an initial segment in its original order, not merely a subset.

`Completion R P a b` is defined using the position of an entry in `P`:

```lean
P.idxOf a < P.idxOf b ∨ (a ∉ P ∧ b ∉ P ∧ R a b)
```

For a missing entry, `idxOf` returns the length of the list. Consequently:

- two entries of the word are compared by their positions;
- every entry of the word precedes every missing entry;
- two missing entries are compared by `R`.

This is exactly `𝒞(P)`. The file `FourAP/Completion.lean` proves these facts,
the strict order laws, and the fact that an old prefix stays at the beginning
of an extended completion. `Safe R P` includes both `P.Nodup` and 4AP-freeness
of the completion.

## 5. Lemma 1 and the parity words

`FourAP/Words.lean` contains Lemma 1 as `safe_of_reverse_pairwise`.
`P.Pairwise (fun a b => bits b a)` means that every earlier-later pair in `P`
is in reverse binary order.

The proof has the same three cases as the paper. If the third AP term is in
the prefix, the first three contradict reverse-order 3AP-freeness. If the
second term is in the prefix but the third is not, equation (1) contradicts
the two opposite comparisons. Otherwise the final three terms contradict
3AP-freeness in the tail.

`parityWord p P` keeps entries whose remainder modulo two is `p`, then divides
them by two. For `p=1`, this agrees with `(t-1)/2` because `t` is odd.
`completion_parity` proves equality of the relevant comparisons after
restriction and rescaling. `safe_parity` transports the absence of APs;
its proof explicitly maps an AP back by `x ↦ 2*x+p`.

## 6. Reading the Extension Lemma

The longest proof is divided into three files to keep the mathematics visible.

1. **`Splice.lean`: the final contradiction.**
   `safe_of_parity_and_guard` assumes that each parity restriction is safe,
   the old prefix remains fixed, and every unplaced odd `y ≤ 2*x` precedes
   an unplaced even `x`. It then follows the paper's exact case analysis:
   equal parity is impossible; the third and fourth terms are new; an even
   third term contradicts the guard; with an odd third term, the second term
   must also be new and gives the other guard contradiction.
2. **`Glue.lean`: verifying those hypotheses for `P O E`.**
   `safe_splice` takes the two safe parity extensions. It identifies the two
   parity projections of the concatenated word, proves distinctness, and
   establishes equation (2). The formal parameters `E` and `O` in this file
   are *normalized suffixes*. They are mapped back by `2*x` and `2*x+1`
   when appended, whereas the paper calls the rescaled suffixes `E` and `O`.
3. **`Extension.lean`: the recursive construction and its induction proof.**
   `extendAlgorithm` first extends the even word, computes the largest
   rescaled new even entry `h` (zero for an empty suffix), and then extends
   the odd word with the normalized odd targets together with every integer
   below `h`.
   `extendAlgorithm_spec` proves safety using `safe_splice`, together with
   preservation of the old prefix and coverage of the target set.

The recursion measure is the largest entry `m` of the old word, taken as zero
when the word is empty. Every parity entry is at most `m/2`, and `m/2<m` when
`m>0`. The target is universally quantified throughout the induction. The
base case uses reverse sorting and the fact that zero comes first in reverse
binary order. The existential statement `safe_extend` is an immediate corollary
whose witness is the computed extension; it needs no second induction.

## 7. The infinite permutation

`FourAP/Limit.lean` gives the union-of-prefixes argument for a sequence of safe
words. If stage `n` contains all values below `n`, then its length is at least
`n`. Prefix compatibility proves that a position's value, and a value's
position, cannot change once they have appeared.

Both directions of the bijection are explicit. The value at position `i` can
be read in stage `i+1`, and the position of value `t` can be found in stage
`t+1`. The proofs show that these functions are mutually inverse. The default
in the list lookup is proved unreachable. These bounds ensure total
computation; stabilization permits stopping at an earlier adequate stage.

Any four proposed AP entries can be read in one safe stage, producing the
final contradiction. This single construction proves both the existence
assertion and the effective claim in the remark.

## 8. The particular construction and the Python port

In `FourAP/Construction.lean`, `algorithmStage` iterates the proved extension
with `{0}`, `{1}`, `{2}`, and so on. `algorithmStage_covers` proves by induction
that stage `n` contains every value below `n`. Thus singleton targets satisfy
the hypothesis of the union-of-prefixes theorem.

`explicitPermutation` and `explicitPositivePermutation` are the resulting
computable bijections. Their avoidance theorems imply the main existence
theorem simply by providing these explicit witnesses.

Both printed prefixes have separate proofs in `FourAP/Examples.lean`,
identifying them with the actual bijections' initial values. For kernel
evaluation, the reverse listing has an insertion-sort implementation proved
equal to the mathematical reverse listing. This changes only how the sorted
list is computed. The numerical proof uses `decide +kernel`.

The Python function `_extend_suffix` in `four_ap.py` follows the same recursion
using compact words. It computes normalized even and odd suffixes and records
their rescaling and concatenation as `O E`; the old prefix is preserved
separately. Forced target intervals are stored as endpoints rather than sets
of all their integers. [PERFORMANCE.md](PERFORMANCE.md) explains the four word
representations, parity-count lookup, and their relationship to the proof.

`Permutation` stores compact descriptions of its stages and caches requested
forward and inverse answers. A query advances until its answer is present,
then uses block lengths or value parity to choose the relevant branches.
It does not enumerate a whole stage. The positive mode shifts values
by one while keeping Python positions zero-based.

The public `extend(prefix, targets)` returns a new explicit list and
checks its output length before materialization. Its keyword-only
`max_length` defaults to 100,000 total entries; excessive results raise
`OverflowError`. The configurable limit can be raised or explicitly disabled
with `None`, but Python's maximum list length remains enforced. This guards
output size and bounds the number of distinct input values consumed, but it
does not limit every possible cost of consuming inputs or building a plan.

Tests compare entire small Python stages and finite-target extensions with
Lean's outputs and check the compact implementation against a literal
list/set implementation of the Extension Lemma. They also exercise large
forward/inverse queries and size-guard failures. The infinite correctness
proof is in Lean. Compact stages avoid enormous unrequested output, but
constructing more distant stages can be costly.

## 9. A few Lean conventions

- `h : P` names a proof of proposition `P`; `⟨h₁, h₂⟩` constructs a conjunction
  or a structure with two fields.
- `intro` introduces a variable or assumption. `rcases` and `obtain` unpack
  alternatives or existential witnesses. `by_cases` splits a mathematical case.
- `simp` applies established rewriting rules. `omega` proves the remaining
  natural/integer linear arithmetic, including the fixed-modulus parity and
  division facts used here.
- `rw` rewrites by an equality or equivalence. A `termination_by` declaration
  names the decreasing measure of a recursive definition or proof.
- `#eval` runs an example. `#print axioms` inspects a theorem's logical
  dependencies. `FourAP/Audit.lean` checks the main theorem's statement and
  enforces the permitted axiom list for the key results.

Every theorem still passes through Lean's kernel, regardless of which tactics
produce its proof. The mathematical content is in the statements, recursive
constructions, and case analyses; the arithmetic tactics handle the small
calculations between those steps.

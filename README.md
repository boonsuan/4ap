# A 4AP-free permutation of the positive integers

This repository formalizes the paper *A 4AP-free permutation of the
positive integers* in **Lean 4 with mathlib**. It also provides a readable
**Python implementation of the permutation and its inverse**.

**Paper on arXiv:** *link forthcoming.*
<!-- TODO: Replace the placeholder above with the paper's arXiv link. -->

The formalization proves the binary-order properties, both lemmas, the main
theorem, and the computability remark, including both displayed fifteen-term
prefixes. The existence theorem uses the explicit computable permutation as its
witness. Historical results cited in the introduction are background, not
assumptions in the proof. The paper itself is not included in this repository.

## Where to start

- **Read the theorem:** [the main Lean statement](#the-main-theorem) below,
  with its proof in [FourAP/Main.lean](FourAP/Main.lean).
- **Follow the paper's proof:** use the [paper-to-code table](#paper-to-code-correspondence)
  or the [mathematical reading guide](MATHEMATICAL_GUIDE.md), which explains
  the representations, proof structure, and Lean notation.
- **Compute examples:** [four_ap.py](four_ap.py) implements the recursive
  extension, permutation, and inverse; [usage examples](#generate-the-permutation-and-its-inverse-in-python)
  appear below.
- **Check the formalization:** follow the [build instructions](#build-and-check).
  [FourAP.lean](FourAP.lean) imports the theorem and proved numerical examples;
  [Examples.lean](Examples.lean) prints the examples.
- **Inspect verification:** [tests/](tests/) contains Python tests and a Lean
  comparison program; [FourAP/Audit.lean](FourAP/Audit.lean) reports proof axioms.
  [CI](.github/workflows/ci.yml) runs the checks on GitHub.

## The main theorem

[`FourAP/Main.lean`](FourAP/Main.lean) contains
`FourAP.exists_fourAPFree_positive_permutation`. Here is the full statement
and its short final proof, as written inside `namespace FourAP`:

```lean
theorem exists_fourAPFree_positive_permutation :
    ∃ f : ℕ+ ≃ ℕ+, ∀ i j k l : ℕ+,
      i < j → j < k → k < l → ∀ a r : ℤ, r ≠ 0 →
      ¬ (((f i : ℕ) : ℤ) = a ∧ ((f j : ℕ) : ℤ) = a + r ∧
         ((f k : ℕ) : ℤ) = a + 2 * r ∧ ((f l : ℕ) : ℤ) = a + 3 * r) :=
  ⟨explicitPositivePermutation, explicitPositivePermutation_apFree⟩
```

Here `ℕ+` denotes positive integers, and `≃` is a bijection with an inverse:
no value is omitted or repeated. Both indices and values in this theorem are
positive. The common difference lies in `ℤ`, so decreasing progressions are
excluded too.

The witness is `explicitPositivePermutation`, defined in
[`FourAP/Construction.lean`](FourAP/Construction.lean). Its forward and inverse
maps are executable. The theorem `explicitPositivePermutation_apFree` proves
the displayed avoidance property for that specific bijection.

## Key definitions and the construction

The following excerpts are also inside `namespace FourAP`. Lean's `ℕ` includes
zero, so the finite-word construction takes place on the nonnegative integers.
In [Basic.lean](FourAP/Basic.lean), the predicate for an arithmetic progression is:

```lean
def IsAP4 (a b c d : ℕ) : Prop :=
  a ≠ b ∧ a + c = 2 * b ∧ b + d = 2 * c
```

The theorem `isAP4_iff_integer_progression` proves that these equations are
equivalent to a nonzero integer common difference, including negative ones.
The completion and safety definitions encode the paper's `𝒞(P)` and safe words:

```lean
def APFree (R : ℕ → ℕ → Prop) : Prop :=
  ∀ ⦃a b c d : ℕ⦄, IsAP4 a b c d → R a b → R b c → R c d → False

def Completion (R : ℕ → ℕ → Prop) (P : List ℕ) (a b : ℕ) : Prop :=
  P.idxOf a < P.idxOf b ∨ (a ∉ P ∧ b ∉ P ∧ R a b)

def Safe (R : ℕ → ℕ → Prop) (P : List ℕ) : Prop :=
  P.Nodup ∧ APFree (Completion R P)
```

`P.idxOf a` is the position of `a`, or `P.length` if `a` is absent. Thus this
completion puts the word first, then compares missing entries by `R`.
Taking `R = bits` gives the paper's binary-order completion; `P.Nodup` means
that the word has no repeated entries.

The Extension Lemma is [Extension.lean](FourAP/Extension.lean)'s `safe_extend`:

```lean
theorem safe_extend (P : List ℕ) (hP : Safe bits P) (T : Finset ℕ) :
    ∃ Q, Safe bits Q ∧ P.IsPrefix Q ∧ ∀ t ∈ T, t ∈ Q :=
  ⟨extendAlgorithm P T, extendAlgorithm_spec P T hP⟩
```

Here `P.IsPrefix Q` means that `Q` begins with the entries of `P` in their
original order. The witness is the recursive algorithm itself, whose
correctness is proved by `extendAlgorithm_spec`.

[Construction.lean](FourAP/Construction.lean) then uses the singleton targets
from the paper's final proof and remark:

```lean
def algorithmStage : ℕ → List ℕ
  | 0 => []
  | n + 1 => extendAlgorithm (algorithmStage n) {n}
```

Safety, prefix compatibility, and coverage are proved for these stages.
[Limit.lean](FourAP/Limit.lean) turns them into a bijection, with explicit forward
and inverse maps, and proves that it avoids every nonconstant 4AP. Shifting
values and positions by one produces the witness in the main theorem above.

## Paper-to-code correspondence

All declarations below belong to the namespace `FourAP`. Module introductions,
declaration documentation, and comments at the main proof steps explain the
correspondence with the paper.

| Part of the paper | File | Main declarations |
| --- | --- | --- |
| Nonconstant APs, including negative differences | [Basic](FourAP/Basic.lean) | `IsAP4`, `isAP4_iff_integer_progression`, `APFree` |
| Completion `𝒞(P)` and safe words | [Basic](FourAP/Basic.lean), [Completion](FourAP/Completion.lean) | `Completion`, `Safe`, order and prefix lemmas |
| Least differing bit defines `◁` | [Binary](FourAP/Binary.lean) | `bits`, `bits_iff_first_differing_bit` |
| Parity self-similarity and zero greatest | [Binary](FourAP/Binary.lean) | `bits_parity`, `bits_odd_even`, `bits_zero` |
| 3AP-freeness of `◁` and its dual; equation (1) | [Binary](FourAP/Binary.lean) | `bits_no_three_of_eq`, `bits_dual_no_three`, `bits_pairs` |
| Lemma 1: reverse binary listings are safe | [Words](FourAP/Words.lean) | `safe_of_reverse_pairwise`, `safe_reverseWord` |
| Safe parity words `P₀` and `P₁` | [Words](FourAP/Words.lean) | `parityWord`, `completion_parity`, `safe_parity` |
| Lemma 2: `Q = P O E`, equation (2), and the final contradiction | [Glue](FourAP/Glue.lean), [Splice](FourAP/Splice.lean) | `safe_splice`, `safe_of_parity_and_guard` |
| Lemma 2: recursive construction and its proof | [Extension](FourAP/Extension.lean) | `extendAlgorithm`, `extendAlgorithm_spec`, `safe_extend` |
| Union of safe prefixes, including an explicit inverse | [Limit](FourAP/Limit.lean) | `permutationOfSafeStages`, `permutationOfSafeStages_apFree` |
| Singleton stages and the positive permutation | [Construction](FourAP/Construction.lean) | `algorithmStage`, `explicitPermutation`, `explicitPositivePermutation` |
| Main existence theorem | [Main](FourAP/Main.lean) | `exists_fourAPFree_positive_permutation` |
| Both printed fifteen-term prefixes | [Examples](FourAP/Examples.lean) | `explicitPermutation_paper_prefix`, `explicitPositiveSequence_paper_prefix` |

[`MATHEMATICAL_GUIDE.md`](MATHEMATICAL_GUIDE.md) gives a reading guide for
mathematicians less familiar with Lean.

## Generate the permutation and its inverse in Python

```python
from four_ap import Permutation

p = Permutation()
p.prefix(15)
# [0, 1, 3, 2, 11, 7, 15, 9, 5, 6, 4, 2063, 1039, 527, 2575]
p.value(11)       # 2063
p.position(2063)  # 11: the inverse
```

An instance keeps compact descriptions of its stages and caches queried
forward and inverse answers. It stops at the first adequate stage without
enumerating that entire stage. Iteration yields the infinite sequence; use a
finite consumer such as `itertools.islice(p, 15)`.

```python
first_thousand = p.prefix(1000)
term = Permutation().value(999)  # Does not compute the preceding 999 entries.
assert Permutation().position(term) == 999  # Also works with an empty cache.
```

See [the implementation guide and benchmarks](PERFORMANCE.md) for the compact
representation, its relationship to the proof, and performance limitations.

`Permutation(positive=True)` adds one to every value:

```python
q = Permutation(positive=True)
q.prefix(15)
# [1, 2, 4, 3, 12, 8, 16, 10, 6, 7, 5, 2064, 1040, 528, 2576]
q.value(11)       # 2064
q.position(2064)  # 11
```

**Python positions are always zero-based**, including in positive mode. For
the paper's one-based permutation, `a_j = q.value(j - 1)` and the inverse
position of a value `v` is `q.position(v) + 1`.

The same operations are available from the command line:

```sh
python3 four_ap.py --count 15
python3 four_ap.py --positive --count 15
python3 four_ap.py --index 11
python3 four_ap.py --inverse 2063
```

The function `extend(prefix, targets)` exposes Lemma 2 directly. It returns a
new list and leaves its inputs unchanged. As in the lemma, its prefix must be
a *safe word*. It validates natural-number entries and distinctness; it does
not decide safety for arbitrary user input.

**Explicit extensions are size-guarded.** By default `extend` raises
`OverflowError` if its result would exceed 100,000 entries, including the old
prefix. It checks a lower bound while reading input values and computes the
exact size compactly before enumerating appended output entries.
For deliberately materialized results, pass a larger keyword-only
`max_length`, or `max_length=None` to disable the configurable limit. Python's
maximum list length is still enforced. The guard is an output-count limit,
not a guarantee about runtime or memory; inputs and compact plans can also
be expensive. Prefer `Permutation().prefix(n)` or `.value(k)` for canonical
queries instead of explicitly expanding an entire stage.

The paper's construction has rapidly growing stages. Compact representations
make the first 1,000 terms practical, but more distant stages may themselves
be costly to build. The construction is formally proved in Lean; the Python
implementation is tested against it, not itself formally verified.

## Build and check

The project pins **Lean 4.33.1** and **mathlib v4.33.1** (commit
`0df444a360eaa60ab8c11dca51a86af692955474`). Transitive dependencies are pinned in
`lake-manifest.json`.

With [elan](https://github.com/leanprover/elan) installed:

```sh
git clone https://github.com/boonsuan/4ap.git
cd 4ap
lake exe cache get
lake build --wfail
lake lint
lake env lean Examples.lean
lake env lean FourAP/Audit.lean
python3 -m doctest four_ap.py
python3 -m unittest discover -s tests -v
```

`lake exe cache get` fetches precompiled mathlib dependencies and is needed
only when the cache is missing. elan selects the pinned Lean version automatically.
If `lake` is missing from an existing terminal's PATH, run
`source "$HOME/.elan/env"` first.

Python requires **3.10 or later**, with no third-party packages. Its unit tests
run without Lean; the cross-language test additionally runs when `lake` is on
PATH and compares the first ten complete stages and several finite-target
extensions against the proved Lean functions.

For interactive proof reading, open this directory in an editor supporting
Lean 4. `.vscode/extensions.json` recommends the `leanprover.lean4` extension.

## Representation and proof choices

- Lean's `ℕ` includes zero. Construction on `ℕ` precedes the shift to `ℕ+`.
- `IsAP4` uses `a+c=2*b`, `b+d=2*c`, and `a≠b`.
  `isAP4_iff_integer_progression` proves equivalence with a nonzero integer
  common difference, avoiding truncated natural subtraction.
- Binary order is an explicit relation with proved order laws. Lean's usual
  numerical comparisons on naturals retain their ordinary meaning.
- There is one extension proof and one union-of-prefixes proof, both for the
  computable construction. All stages use the paper's singleton targets `{n}`.
- An insertion-sort implementation of the finite reverse listing is proved
  equal to mathlib's sorted list, allowing kernel evaluation of the example.
- Finite numerical proofs are in `FourAP/Examples.lean`; importing
  `FourAP.Main` needs only the general construction.

`lake env lean Examples.lean` prints the eight-element binary-order example
and both fifteen-term prefixes. The corresponding equalities with the actual
infinite permutations are kernel-checked theorems, not merely demonstrations
that those finite lists avoid APs.

## Verification

`lake build --wfail` checks all proofs with implicit-variable inference disabled and
mathlib's standard syntax linters enabled; warnings fail the build. Copyright
and license headers are checked against this project's MIT license.
`lake lint` runs the mathematical declaration linters.

[`FourAP/Audit.lean`](FourAP/Audit.lean) checks a direct restatement of the main
theorem using standard mathematical types. It also reports the axioms used by
the key results and fails if any fall outside the permitted list:

```text
[propext, Classical.choice, Quot.sound]
```

There are no `sorry` declarations, custom axioms, or native-evaluation axioms.
The Python tests check the displayed prefixes, forward/inverse agreement,
input handling, both AP directions in finite samples, and complete output
agreement with Lean through stage 9 (354 entries).

The [GitHub Actions workflow](.github/workflows/ci.yml) runs the Lean build and
linters, proof-axiom audit, Python documentation examples, and Python tests
(including comparison with Lean) on every push and pull request.

## License

The code and documentation in this repository are released under the
[MIT License](LICENSE). Dependencies, including Lean and mathlib, retain their
own licenses.

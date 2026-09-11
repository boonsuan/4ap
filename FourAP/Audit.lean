/-
Copyright (c) 2026 Boon Suan Ho. All rights reserved.
Released under MIT license as described in the file LICENSE.
Authors: Boon Suan Ho
-/
import FourAP.Main
import FourAP.Examples
import Lean.Elab.Command
import Lean.Util.CollectAxioms

/-!
# Theorem statement and kernel dependency audit

This file makes the trust boundary of the paper's formalization inspectable.
Run `lake env lean FourAP/Audit.lean` to check the main theorem's statement and
the axioms used by the key results. An unexpected axiom is an error, so this
command fails in CI as well as locally. The only permitted axioms are
`propext`, `Classical.choice`, and `Quot.sound`.

The statement below is deliberately written out using standard mathematical
types, without any of the project's AP predicates. It checks that the main
theorem still proves the paper's assertion, including negative differences.
This file is a regression check and is not imported by the mathematical proofs.
-/

example : ∃ f : ℕ+ ≃ ℕ+, ∀ i j k l : ℕ+,
    i < j → j < k → k < l → ∀ a r : ℤ, r ≠ 0 →
    ¬ (((f i : ℕ) : ℤ) = a ∧ ((f j : ℕ) : ℤ) = a + r ∧
       ((f k : ℕ) : ℤ) = a + 2 * r ∧ ((f l : ℕ) : ℤ) = a + 3 * r) :=
  @FourAP.exists_fourAPFree_positive_permutation

/-- Report a declaration's axioms and reject any outside the standard three.
Name resolution also makes a missing or misspelled audit target an error. -/
elab "check_standard_axioms " n:ident : command => do
  let name ← Lean.Elab.Command.liftCoreM <| Lean.Elab.realizeGlobalConstNoOverloadWithInfo n
  let axioms ← Lean.collectAxioms name
  let permitted := #[``propext, ``Classical.choice, ``Quot.sound]
  let unexpected := axioms.filter fun ax => !permitted.contains ax
  unless unexpected.isEmpty do
    throwError "{name} uses unexpected axioms: {unexpected.toList}"
  Lean.logInfo m!"{name} depends on axioms: {axioms.toList}"

-- The order defined before Lemma 1 is the paper's first-differing-bit order.
check_standard_axioms FourAP.bits_iff_first_differing_bit

-- Lemma 1: reverse binary listings of finite sets are safe.
check_standard_axioms FourAP.safe_of_reverse_pairwise

-- Lemma 2: every safe finite prefix has a safe extension covering any target.
check_standard_axioms FourAP.safe_extend

-- The paper's main theorem, with positive indices, positive values, and
-- arbitrary nonzero integer common differences.
check_standard_axioms FourAP.exists_fourAPFree_positive_permutation

-- The executable recursive extension satisfies all three conclusions of Lemma 2.
check_standard_axioms FourAP.extendAlgorithm_spec

-- The computable union of singleton-target stages is the promised permutation.
check_standard_axioms FourAP.explicitPermutation_apFree

-- The stage computation underlying the final remark is kernel checked.
check_standard_axioms FourAP.algorithmStage_nine_example

-- The displayed prefix belongs to the actual infinite permutation.
check_standard_axioms FourAP.explicitPermutation_paper_prefix

-- The explicitly constructed positive permutation satisfies the full theorem.
check_standard_axioms FourAP.explicitPositivePermutation_apFree

-- Adding one gives the second displayed prefix in the final remark.
check_standard_axioms FourAP.explicitPositiveSequence_paper_prefix

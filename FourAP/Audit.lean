/-
Copyright (c) 2026 Boon Suan Ho. All rights reserved.
Released under MIT license as described in the file LICENSE.
Authors: Boon Suan Ho
-/
import FourAP.Main
import FourAP.Examples

/-!
# Kernel dependency audit

This file makes the trust boundary of the paper's formalization inspectable.
Run `lake env lean FourAP/Audit.lean` to print the axioms used by the semantic
identification of the binary order, Lemma 1, Lemma 2, the final theorem, and
the executable construction in the concluding remark. The numerical example
is checked in Lean's kernel, so its audit includes no native-evaluation axiom.
-/

-- The order defined before Lemma 1 is the paper's first-differing-bit order.
#print axioms FourAP.bits_iff_first_differing_bit

-- Lemma 1: reverse binary listings of finite sets are safe.
#print axioms FourAP.safe_of_reverse_pairwise

-- Lemma 2: every safe finite prefix has a safe extension covering any target.
#print axioms FourAP.safe_extend

-- The paper's main theorem, with positive indices, positive values, and
-- arbitrary nonzero integer common differences.
#print axioms FourAP.exists_fourAPFree_positive_permutation

-- The executable recursive extension satisfies all three conclusions of Lemma 2.
#print axioms FourAP.extendAlgorithm_spec

-- The computable union of singleton-target stages is the promised permutation.
#print axioms FourAP.explicitPermutation_apFree

-- The stage computation underlying the final remark is kernel checked.
#print axioms FourAP.algorithmStage_nine_example

-- The displayed prefix belongs to the actual infinite permutation.
#print axioms FourAP.explicitPermutation_paper_prefix

-- The explicitly constructed positive permutation satisfies the full theorem.
#print axioms FourAP.explicitPositivePermutation_apFree

-- Adding one gives the second displayed prefix in the final remark.
#print axioms FourAP.explicitPositiveSequence_paper_prefix

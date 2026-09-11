/-
Copyright (c) 2026 Boon Suan Ho. All rights reserved.
Released under MIT license as described in the file LICENSE.
Authors: Boon Suan Ho
-/
import FourAP.Examples

/-!
# Running the examples from the paper

Run `lake env lean Examples.lean` in the project directory.

These commands are demonstrations, not proof oracles. The equalities with the
actual infinite permutations are proved in `FourAP/Examples.lean` as
`explicitPermutation_paper_prefix` and `explicitPositiveSequence_paper_prefix`.

Stage 9 is already long enough to read the fifteen displayed entries.
Using a sufficient early stage avoids computing the larger bound used in
the simple definition of the infinite permutation.
-/

open FourAP

-- The reverse colexicographical order on the three-bit strings, before Lemma 1.
#eval (reverseWord (Finset.range 8)).reverse

-- The displayed nonnegative-integer prefix in the final remark.
#eval (algorithmStage 9).take 15

-- The displayed positive-integer prefix, obtained by adding one to each value.
#eval ((algorithmStage 9).take 15).map (fun n => n + 1)

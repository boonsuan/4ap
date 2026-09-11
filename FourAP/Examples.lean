/-
Copyright (c) 2026 Boon Suan Ho. All rights reserved.
Released under MIT license as described in the file LICENSE.
Authors: Boon Suan Ho
-/
import FourAP.Construction

/-!
# The numerical prefixes in the paper's remark

This file verifies the two fifteen-term prefixes printed in Boon Suan Ho's
“A 4AP-free permutation of the positive integers”. Stage 9 is long enough to
read all fifteen entries. The finite computation is checked by Lean's kernel;
stabilization then identifies its output with the actual infinite permutations.

These computations are separate from the proof of the general construction.
-/

namespace FourAP

set_option maxRecDepth 10000 in
set_option maxHeartbeats 2000000 in
-- Kernel reduction of nine recursive stages needs a larger heartbeat budget.
/-- The fifteen terms printed in the final remark, computed at stage 9.
The proof evaluates the executable construction in Lean's kernel; it does
not use a native-code evaluation axiom. -/
theorem algorithmStage_nine_example :
    (algorithmStage 9).take 15 =
      [0, 1, 3, 2, 11, 7, 15, 9, 5, 6, 4, 2063, 1039, 527, 2575] := by
  decide +kernel

/-- The paper's displayed prefix is an initial segment of the proved
4AP-free permutation itself, by stabilization of finite stages. -/
theorem explicitPermutation_paper_prefix :
    (List.range 15).map explicitPermutation =
      [0, 1, 3, 2, 11, 7, 15, 9, 5, 6, 4, 2063, 1039, 527, 2575] := by
  have hlen := congrArg List.length algorithmStage_nine_example
  simp only [List.length_take, List.length_cons, List.length_nil] at hlen
  rw [explicitPermutation_prefix 9 15 (by omega)]
  exact algorithmStage_nine_example

/-- The second displayed prefix in the final remark is the beginning of the
proved positive sequence, obtained by adding one to the first prefix. -/
theorem explicitPositiveSequence_paper_prefix :
    (List.range 15).map (fun i => (explicitPositiveSequence i : ℕ)) =
      [1, 2, 4, 3, 12, 8, 16, 10, 6, 7, 5, 2064, 1040, 528, 2576] := by
  calc
    _ = ((List.range 15).map explicitPermutation).map (fun n => n + 1) := by
      simp only [List.map_map, Function.comp_def, explicitPositiveSequence_apply]
    _ = _ := by
      rw [explicitPermutation_paper_prefix]
      rfl

end FourAP

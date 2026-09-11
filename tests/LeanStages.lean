/-
Copyright (c) 2026 Boon Suan Ho. All rights reserved.
Released under MIT license as described in the file LICENSE.
Authors: Boon Suan Ho
-/
import FourAP.Construction
import Lean.Data.Json.FromToJson.Basic
import Lean.Data.Json.Printer

/-!
# Reference outputs for the Python cross-language test

Print the first ten complete singleton-target stages, followed by extensions
of arbitrary finite targets from a safe reverse-listed prefix. These outputs
come from the proved Lean construction. The Python tests compare full lists,
including the many stage-9 entries beyond the paper's displayed prefix.
-/

open FourAP

-- JSON serialization avoids the truncation used by Lean's display printer.
#eval IO.println (Lean.toJson ([
  (List.range 10).map algorithmStage,
  ([∅, {6}, {0, 7}, {2, 8}] : List (Finset ℕ)).map
    (extendAlgorithm (reverseWord (Finset.range 6)))
] : List (List (List ℕ)))).compress

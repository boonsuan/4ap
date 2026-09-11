/-
Copyright (c) 2026 Boon Suan Ho. All rights reserved.
Released under MIT license as described in the file LICENSE.
Authors: Boon Suan Ho
-/
import FourAP.Main
import FourAP.Examples

/-!
# A 4AP-free permutation of the positive integers

Formalization of the paper “A 4AP-free permutation of the positive integers”.
The main existence theorem is `FourAP.exists_fourAPFree_positive_permutation`.
The particular computable permutation from the final remark is
`FourAP.explicitPositivePermutation`, with correctness theorem
`FourAP.explicitPositivePermutation_apFree`.

See `README.md` for build instructions and the paper-to-code correspondence,
and `MATHEMATICAL_GUIDE.md` for a guided reading of the proofs.
-/

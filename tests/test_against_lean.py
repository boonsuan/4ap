# Copyright (c) 2026 Boon Suan Ho
# SPDX-License-Identifier: MIT

"""Compare the Python port with the proved Lean construction.

This integration test is skipped when Lake is not on PATH. The ordinary Python
unit tests need only the standard library. With Lean installed, first run
``lake build``, then ``python3 -m unittest discover -s tests -v``.
"""

import json
from pathlib import Path
import shutil
import subprocess
import unittest

from four_ap import extend


ROOT = Path(__file__).resolve().parents[1]
LAKE = shutil.which("lake")


@unittest.skipUnless(LAKE, "Lake is not on PATH; Lean cross-language test skipped")
class LeanAgreementTests(unittest.TestCase):
    def test_complete_stages_and_arbitrary_targets(self):
        result = subprocess.run(
            [LAKE, "env", "lean", "tests/LeanStages.lean"], cwd=ROOT,
            capture_output=True, text=True, timeout=120, check=True,
        )
        outputs = json.loads(result.stdout)
        self.assertEqual(len(outputs), 2, result.stdout)
        stages, target_extensions = outputs
        self.assertEqual(len(stages), 10)
        self.assertEqual(stages[0], [])
        word = []
        for n, expected in enumerate(stages[1:]):
            with self.subTest(stage=n + 1):
                word = extend(word, {n})
                self.assertEqual(word, expected)
        self.assertEqual(len(word), 354)
        self.assertEqual(len(target_extensions), 4)
        base = extend([], range(6))
        for targets, expected in zip((set(), {6}, {0, 7}, {2, 8}), target_extensions):
            with self.subTest(targets=targets):
                self.assertEqual(extend(base, targets), expected)


if __name__ == "__main__":
    unittest.main()

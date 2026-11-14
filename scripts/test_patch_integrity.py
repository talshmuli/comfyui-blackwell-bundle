import os
import re
import unittest

class TestPatchIntegrity(unittest.TestCase):
    def setUp(self):
        self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.patches_dir = os.path.join(self.root_dir, "patches")

    def test_patch_files_exist_and_non_empty(self):
        patch_files = [f for f in os.listdir(self.patches_dir) if f.endswith(".patch")]
        self.assertGreater(len(patch_files), 0, "No patch files found in patches/")
        for pf in patch_files:
            p_path = os.path.join(self.patches_dir, pf)
            self.assertGreater(os.path.getsize(p_path), 0, f"Patch file {pf} is empty")

    def test_comfy_path_resilience_patch_syntax(self):
        patch_path = os.path.join(self.patches_dir, "comfy_path_resilience.patch")
        self.assertTrue(os.path.isfile(patch_path), "comfy_path_resilience.patch does not exist")
        with open(patch_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # Verify no lines in hunks start with un-prefixed indentation inside additions
        in_hunk = False
        for idx, line in enumerate(lines):
            if line.startswith("@@"):
                in_hunk = True
                continue
            if line.startswith("diff --git"):
                in_hunk = False
                continue
            if in_hunk:
                # Every line inside a diff hunk must start with ' ', '+', '-', or '\'
                self.assertTrue(
                    line[0] in (" ", "+", "-", "\\", "\n"),
                    f"Line {idx+1} in {patch_path} has invalid diff prefix: {line!r}"
                )
                # Specific check for lines 28-29 bug: val = norm_val and inputs[x] = val must have '+'
                if "val = norm_val" in line or "inputs[x] = val" in line:
                    self.assertTrue(
                        line.startswith("+"),
                        f"Line {idx+1} in {patch_path} must start with '+' for diff addition: {line!r}"
                    )

if __name__ == "__main__":
    unittest.main()

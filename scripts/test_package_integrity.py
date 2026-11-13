#!/usr/bin/env python3
import os
import re
import unittest

class TestPackageIntegrity(unittest.TestCase):
    def test_dockerfile_no_duplicate_librosa(self):
        dockerfile_path = os.path.join(os.path.dirname(__file__), "..", "Dockerfile")
        with open(dockerfile_path, "r", encoding="utf-8") as f:
            content = f.read()
        matches = re.findall(r'^\s*librosa\s*\\?$', content, re.MULTILINE)
        self.assertEqual(len(matches), 1, f"Expected exactly 1 librosa entry in Dockerfile, found {len(matches)}")

    def test_dockerfile_declares_helper_packages(self):
        dockerfile_path = os.path.join(os.path.dirname(__file__), "..", "Dockerfile")
        with open(dockerfile_path, "r", encoding="utf-8") as f:
            content = f.read()
        for pkg in ("zipp", "lightning-utilities", "tomli", "mako", "sympy>=1.13.3"):
            self.assertIn(pkg, content, f"Missing package {pkg} in Dockerfile")

if __name__ == "__main__":
    unittest.main()

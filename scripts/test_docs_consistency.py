#!/usr/bin/env python3
import json
import os
import unittest


class TestDocsConsistency(unittest.TestCase):
    def test_all_catalog_nodes_mentioned_in_readme(self):
        catalog_path = os.path.join(os.path.dirname(__file__), "..", "custom_nodes.json")
        readme_path = os.path.join(os.path.dirname(__file__), "..", "README.md")
        with open(catalog_path, "r", encoding="utf-8") as f:
            catalog = json.load(f)
        with open(readme_path, "r", encoding="utf-8") as f:
            readme = f.read()

        for node in catalog["nodes"]:
            name = node["name"]
            self.assertIn(name, readme, f"Node {name} is in custom_nodes.json but not documented in README.md")

    def test_readme_node_count_is_2106(self):
        readme_path = os.path.join(os.path.dirname(__file__), "..", "README.md")
        with open(readme_path, "r", encoding="utf-8") as f:
            readme = f.read()
        self.assertIn("2,106+", readme, "README.md does not reference verified count 2,106+ nodes")

    def test_contributing_references_validate_image(self):
        contributing_path = os.path.join(os.path.dirname(__file__), "..", "CONTRIBUTING.md")
        with open(contributing_path, "r", encoding="utf-8") as f:
            contributing = f.read()
        self.assertIn("scripts/validate_image.py", contributing, "CONTRIBUTING.md does not reference validate_image.py")


if __name__ == "__main__":
    unittest.main()

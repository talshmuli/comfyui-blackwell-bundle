#!/usr/bin/env python3
import os
import sys
import unittest

# Ensure scripts directory is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from evaluate_trivy import CUSTOM_NODE_DEPS, COMPONENT_DESCRIPTIONS, categorize_location


class TestSecurityScriptResilience(unittest.TestCase):
    def test_new_nodes_categorization_in_trivy(self):
        new_nodes = [
            "custom_nodes/comfyui-crystools",
            "custom_nodes/comfyui-melbandroformer",
            "custom_nodes/comfyui_fl-heartmula",
            "custom_nodes/ace-step-comfyui",
            "custom_nodes/comfyui-step1x-edit",
        ]
        for node_uri in new_nodes:
            cat = categorize_location(node_uri)
            self.assertTrue(
                cat.startswith("Custom Node:"),
                f"Failed categorizing {node_uri}: {cat}",
            )
            self.assertIn(
                cat,
                COMPONENT_DESCRIPTIONS,
                f"Missing description for {cat}",
            )

    def test_new_nodes_dependencies_in_trivy(self):
        expected_deps = {
            "Custom Node: ComfyUI-Crystools": ["pynvml"],
            "Custom Node: ComfyUI-MelBandRoFormer": ["librosa", "soundfile"],
            "Custom Node: ComfyUI_FL-HeartMuLa": ["rotary-embedding-torch"],
            "Custom Node: ACE-Step-ComfyUI": ["diffusers"],
            "Custom Node: ComfyUI-Step1X-Edit": ["qwen-vl-utils"],
        }
        for node_name, pkgs in expected_deps.items():
            self.assertIn(
                node_name,
                CUSTOM_NODE_DEPS,
                f"Missing dependency mapping for {node_name}",
            )
            for pkg in pkgs:
                self.assertIn(
                    pkg,
                    CUSTOM_NODE_DEPS[node_name],
                    f"Package {pkg} missing from {node_name}",
                )

    def test_ast_scan_output_parsing_resilience(self):
        from audit_supply_chain_and_ai_security import parse_ast_scan_output

        # Empty stdout
        self.assertIsNone(parse_ast_scan_output(""))
        self.assertIsNone(parse_ast_scan_output("   \n\n  \t "))
        # Returncode non-zero with empty stdout
        self.assertIsNone(parse_ast_scan_output("", stderr="Error", returncode=1))
        # Valid JSON output with leading logs
        sample_output = "Some log line\nAnother warning\n[[\"HIGH\", \"test.py\", 10, \"eval\"]]\n"
        parsed = parse_ast_scan_output(sample_output)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0][0], "HIGH")


if __name__ == "__main__":
    unittest.main()

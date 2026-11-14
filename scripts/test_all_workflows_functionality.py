#!/usr/bin/env python3
"""Universal Workflow Functionality & Cross-Platform Path Resilience Audit Suite.

Audits all workflows in workflows/ for:
1. Universal discovery of all workflow JSON definitions (>= 160 templates).
2. Complete absence of un-sanitized raw Windows drive paths (e.g. C:\\..., D:/...).
3. Path resilience combo resolution logic simulating ComfyUI execution.py and folder_paths.py patches.
4. Total workflow JSON parse sanity, structure verification, and node statistics (> 1000 nodes).
"""

import json
import os
import re
import sys
import unittest

WIN_DRIVE_PATTERN = re.compile(r"^[a-zA-Z]:[\\/]")
WIN_DRIVE_CONTENT_REGEX = re.compile(r"(?<![a-zA-Z0-9+.-])[a-zA-Z]:(?:\\\\|/)[a-zA-Z0-9_]")


class UniversalWorkflowFunctionalityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cls.workflows_dir = os.path.join(cls.root_dir, "workflows")
        cls.all_workflows = []
        for root, _, files in os.walk(cls.workflows_dir):
            for f in sorted(files):
                if f.endswith(".json"):
                    cls.all_workflows.append(os.path.join(root, f))

    def test_workflow_discovery(self):
        """Verify discovery of all workflow templates across the workflows repository."""
        self.assertGreaterEqual(
            len(self.all_workflows), 160, f"Expected at least 160 workflow files, found {len(self.all_workflows)}"
        )

    def test_zero_raw_windows_drive_letters_in_all_workflows(self):
        """Verify 0 raw Windows drive paths (e.g. C:\\..., D:/...) exist in any workflow."""
        corrupt_files = []

        def check_value(val):
            if isinstance(val, str):
                if WIN_DRIVE_PATTERN.match(val):
                    return True
            elif isinstance(val, dict):
                for v in val.values():
                    if check_value(v):
                        return True
            elif isinstance(val, list):
                for item in val:
                    if check_value(item):
                        return True
            return False

        for wf_path in self.all_workflows:
            with open(wf_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # 1. Content-level regex scan (excluding web protocols http://, https://, file://, etc.)
            if WIN_DRIVE_CONTENT_REGEX.search(content):
                corrupt_files.append(wf_path)
                continue

            # 2. Parsed JSON value traversal
            try:
                data = json.loads(content)
                if check_value(data):
                    corrupt_files.append(wf_path)
            except Exception:
                # If JSON doesn't parse, it will fail in the sanity test
                pass

        self.assertEqual(
            corrupt_files,
            [],
            f"Found un-sanitized Windows drive paths in {len(corrupt_files)} workflow(s): {corrupt_files}",
        )

    def test_windows_drive_detection_unit_logic(self):
        """Unit test confirming detection logic catches Windows drive paths while ignoring URLs."""
        # Genuine Windows drive paths that must be caught
        self.assertTrue(bool(WIN_DRIVE_CONTENT_REGEX.search('{"path": "D:\\\\ComfyUI_windows\\\\output\\\\test.mp4"}')))
        self.assertTrue(bool(WIN_DRIVE_CONTENT_REGEX.search('{"path": "C:/Users/reall/input/foo.png"}')))
        self.assertTrue(bool(WIN_DRIVE_PATTERN.match("D:\\ComfyUI_windows\\ComfyUI\\output\\test.mp4")))
        self.assertTrue(bool(WIN_DRIVE_PATTERN.match("C:/Users/foo/bar.safetensors")))

        # Legitimate URLs, protocols, and text that must NOT be flagged
        self.assertFalse(bool(WIN_DRIVE_CONTENT_REGEX.search('{"url": "https://huggingface.co/Kijai/WanVideo_comfy"}')))
        self.assertFalse(bool(WIN_DRIVE_CONTENT_REGEX.search('{"url": "http://localhost:8188/view"}')))
        self.assertFalse(bool(WIN_DRIVE_CONTENT_REGEX.search('{"notes": "Models:\\n[https://huggingface.co]"}')))
        self.assertFalse(bool(WIN_DRIVE_PATTERN.match("https://huggingface.co/Kijai/WanVideo_comfy")))
        self.assertFalse(bool(WIN_DRIVE_PATTERN.match("wanvideo/Wan2_2_VAE_bf16.safetensors")))

    def test_path_resilience_combo_resolution_logic(self):
        """Simulate ComfyUI execution.py and folder_paths.py path resilience logic."""
        mock_combo_options = {
            "vae": [
                "wanvideo/Wan2_2_VAE_bf16.safetensors",
                "ae.safetensors",
                "sd15/vae-ft-mse-840000-ema-pruned.safetensors",
            ],
            "checkpoints": [
                "sd15/v1-5-pruned-emaonly.ckpt",
                "v1-5-pruned-emaonly.safetensors",
            ],
            "diffusion_models": [
                "WanVideo/2_2/wan2.2_ti2v_5B_fp16.safetensors",
                "wan2.1_t2v_1.3B_bf16.safetensors",
            ],
            "audio": [
                "example.wav",
                "talk.wav",
            ],
            "image": [
                "input_image.png",
                "example.png",
            ],
        }

        # Resolution helper implementing the exact logic from execution.py patch
        def resolve_input(val, combo_options, is_multiselect=False):
            if is_multiselect and isinstance(val, list):
                norm_list = []
                for item in val:
                    if isinstance(item, str) and item not in combo_options:
                        n_item = item.replace("\\", "/")
                        if n_item in combo_options:
                            norm_list.append(n_item)
                        else:
                            b_item = os.path.basename(n_item)
                            m = [
                                opt
                                for opt in combo_options
                                if isinstance(opt, str) and (opt == b_item or os.path.basename(opt) == b_item)
                            ]
                            norm_list.append(m[0] if len(m) == 1 else item)
                    else:
                        norm_list.append(item)
                return norm_list
            else:
                if isinstance(val, str) and val not in combo_options:
                    norm_val = val.replace("\\", "/")
                    if norm_val in combo_options:
                        return norm_val
                    base_val = os.path.basename(norm_val)
                    matches = [
                        opt
                        for opt in combo_options
                        if isinstance(opt, str) and (opt == base_val or os.path.basename(opt) == base_val)
                    ]
                    if len(matches) == 1:
                        return matches[0]
                return val

        # Test Case 1: Raw Windows backslash matches nested option
        self.assertEqual(
            resolve_input("wanvideo\\Wan2_2_VAE_bf16.safetensors", mock_combo_options["vae"]),
            "wanvideo/Wan2_2_VAE_bf16.safetensors",
        )

        # Test Case 2: Flat basename matches nested option
        self.assertEqual(
            resolve_input("Wan2_2_VAE_bf16.safetensors", mock_combo_options["vae"]),
            "wanvideo/Wan2_2_VAE_bf16.safetensors",
        )

        # Test Case 3: Nested backslash matches flat option
        self.assertEqual(
            resolve_input(
                "diffusion_models\\wan2.1_t2v_1.3B_bf16.safetensors",
                mock_combo_options["diffusion_models"],
            ),
            "wan2.1_t2v_1.3B_bf16.safetensors",
        )

        # Test Case 4: Audio fallback matches
        self.assertEqual(
            resolve_input("talk.wav", mock_combo_options["audio"]),
            "talk.wav",
        )

        # Test Case 5: Multiselect list input with mixed backslash and exact match
        self.assertEqual(
            resolve_input(
                ["wanvideo\\Wan2_2_VAE_bf16.safetensors", "ae.safetensors"],
                mock_combo_options["vae"],
                is_multiselect=True,
            ),
            ["wanvideo/Wan2_2_VAE_bf16.safetensors", "ae.safetensors"],
        )

        # Test Case 6: Preserves original if no match exists
        self.assertEqual(
            resolve_input("nonexistent_model.safetensors", mock_combo_options["vae"]),
            "nonexistent_model.safetensors",
        )

        # Test Case 7: Ambiguous matches preserves original value
        ambiguous_options = ["dir_a/model.safetensors", "dir_b/model.safetensors"]
        self.assertEqual(
            resolve_input("model.safetensors", ambiguous_options),
            "model.safetensors",
        )

        # Test Case 8: folder_paths.py get_full_path backslash normalization simulation
        def simulate_folder_paths_lookup(filename, folders_dict):
            if isinstance(filename, str):
                filename = filename.replace("\\", "/")
            filename = os.path.relpath(os.path.join("/", filename), "/")
            for base_dir, files in folders_dict.items():
                full_path = os.path.join(base_dir, filename)
                if full_path in files:
                    return full_path
                base_name = os.path.basename(filename)
                flat_path = os.path.join(base_dir, base_name)
                if flat_path in files:
                    return flat_path
            return None

        mock_disk = {
            "/models/vae": {
                "/models/vae/wanvideo/Wan2_2_VAE_bf16.safetensors",
                "/models/vae/ae.safetensors",
            }
        }
        # Windows nested backslash found in nested folder
        self.assertEqual(
            simulate_folder_paths_lookup("wanvideo\\Wan2_2_VAE_bf16.safetensors", mock_disk),
            "/models/vae/wanvideo/Wan2_2_VAE_bf16.safetensors",
        )
        # Flat basename found in flat directory fallback
        self.assertEqual(
            simulate_folder_paths_lookup("nested\\subdir\\ae.safetensors", mock_disk),
            "/models/vae/ae.safetensors",
        )

    def test_all_170_workflows_json_validity_and_node_sanity(self):
        """Parse all workflow JSON files, assert valid structure, and count node statistics."""
        total_nodes = 0
        total_widgets = 0
        parsed_files = 0

        for wf_path in self.all_workflows:
            with open(wf_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            parsed_files += 1

            nodes = []
            if isinstance(data, dict):
                if "nodes" in data and isinstance(data["nodes"], list):
                    nodes = data["nodes"]
                elif any("class_type" in v for v in data.values() if isinstance(v, dict)):
                    # API prompt format
                    nodes = [v for v in data.values() if isinstance(v, dict) and "class_type" in v]

            total_nodes += len(nodes)
            for node in nodes:
                widgets = node.get("widgets_values", []) if isinstance(node, dict) else []
                if isinstance(widgets, list):
                    total_widgets += len(widgets)

        self.assertEqual(parsed_files, len(self.all_workflows))
        self.assertGreater(total_nodes, 1000, "Expected over 1000 total nodes across all workflows")
        print(
            f"\n[Universal Workflow Audit] Successfully audited {len(self.all_workflows)} workflows, "
            f"{total_nodes} nodes, and {total_widgets} widget configurations."
        )


if __name__ == "__main__":
    unittest.main()

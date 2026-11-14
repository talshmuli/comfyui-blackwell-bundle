#!/usr/bin/env python3
import json
import os
import sys
import tempfile
import unittest

# Ensure scripts dir is on sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from sanitize_workflows import sanitize_path_value, sanitize_workflow_data, scan_workflow_file

class TestWorkflowSanitizer(unittest.TestCase):
    def test_sanitize_path_value_windows_drive_output(self):
        val = "D:\\ComfyUI_windows\\ComfyUI\\output\\latentsync_00036-audio.mp4"
        clean = sanitize_path_value(val)
        self.assertEqual(clean, "output/latentsync_00036-audio.mp4")

    def test_sanitize_path_value_windows_drive_temp(self):
        val = "N:\\AI\\ComfyUI\\temp\\WanVideoWrapper_Fun22ControlCamera_00018.mp4"
        clean = sanitize_path_value(val)
        self.assertEqual(clean, "temp/WanVideoWrapper_Fun22ControlCamera_00018.mp4")

    def test_sanitize_path_value_windows_drive_input(self):
        val = "C:\\Users\\reall\\Softwares\\ComfyUI_windows_portable\\ComfyUI\\input\\Test_CRM_T2I_V2\\RGBA"
        clean = sanitize_path_value(val)
        self.assertEqual(clean, "input/Test_CRM_T2I_V2/RGBA")

    def test_sanitize_path_value_forward_slash(self):
        val = "D:/ComfyUI_windows/ComfyUI/output/preview.mp4"
        clean = sanitize_path_value(val)
        self.assertEqual(clean, "output/preview.mp4")

    def test_sanitize_path_value_relative_model_backslash(self):
        val = "wanvideo\\Wan2_2_VAE_bf16.safetensors"
        clean = sanitize_path_value(val)
        self.assertEqual(clean, "wanvideo/Wan2_2_VAE_bf16.safetensors")

    def test_sanitize_path_value_relative_dot_backslash(self):
        val = ".\\example_workflows\\_Example_Inputs_Files\\dragon_all_renders\\Mask"
        clean = sanitize_path_value(val)
        self.assertEqual(clean, "example_workflows/_Example_Inputs_Files/dragon_all_renders/Mask")

    def test_preserves_urls_and_normal_strings(self):
        url = "https://huggingface.co/Kijai/WanVideo_comfy/tree/main"
        self.assertEqual(sanitize_path_value(url), url)
        text = "Steps:\n1. Run model\n2. Output results"
        self.assertEqual(sanitize_path_value(text), text)

    def test_sanitize_workflow_data_structure(self):
        raw = {
            "nodes": [
                {
                    "id": 1,
                    "videopreview": {
                        "params": {
                            "fullpath": "D:\\ComfyUI_windows\\ComfyUI\\output\\test.mp4"
                        }
                    }
                }
            ]
        }
        cleaned, count = sanitize_workflow_data(raw)
        self.assertEqual(count, 1)
        self.assertEqual(cleaned["nodes"][0]["videopreview"]["params"]["fullpath"], "output/test.mp4")

if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
import json
import os
import sys

ALL_PREINSTALLED_NODES = [
    "ComfyUI-VideoHelperSuite",
    "ComfyUI-WanVideoWrapper",
    "ComfyUI-LTXVideo",
    "ComfyUI-LivePortraitKJ",
    "ComfyUI-LatentSyncWrapper",
    "ComfyUI-3D-Pack",
    "ComfyUI-GGUF",
    "ComfyUI-FL-YuE2",
    "ComfyUI-RVC",
    "ComfyUI-Crystools",
    "ComfyUI-MelBandRoFormer",
    "ComfyUI_FL-HeartMuLa",
    "ACE-Step-ComfyUI",
    "ComfyUI-Step1X-Edit",
    "ComfyUI-KJNodes",
    "ComfyUI_IPAdapter_plus",
    "ComfyUI-AnimateDiff-Evolved",
    "ComfyUI-Frame-Interpolation",
    "comfyui_controlnet_aux",
    "Comfyui-Song-Generation-Suite",
    "ComfyUI-BlenderAI-node"
]

def test_catalog():
    catalog_path = os.path.join(os.path.dirname(__file__), "..", "custom_nodes.json")
    assert os.path.isfile(catalog_path), f"custom_nodes.json not found at {catalog_path}"

    with open(catalog_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "nodes" in data, "Catalog missing 'nodes' key"
    nodes = {node["name"]: node for node in data["nodes"]}

    for name in ALL_PREINSTALLED_NODES:
        assert name in nodes, f"Missing required pre-installed node {name} in catalog"
        node = nodes[name]
        assert node["url"].startswith("https://github.com/"), f"Invalid url for {name}"
        assert "category" in node, f"Missing category for {name}"
        assert "blackwell_verified" in node, f"Missing blackwell_verified flag for {name}"

    print(f"✔ All {len(ALL_PREINSTALLED_NODES)} pre-installed nodes verified in catalog schema.")

if __name__ == "__main__":
    test_catalog()

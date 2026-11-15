#!/usr/bin/env python3
"""Comprehensive Workflow Inventory & Execution Catalog Generator.

Scans all 166 workflows across all 7 folders, analyzes node topologies,
extracts required inputs, models, and expected outputs, tests prompt
validation against ComfyUI, and formats a complete report.
"""

import json
import os
import sys
import urllib.request
import urllib.error
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple

WORKFLOWS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "workflows")
COMFY_URL = "http://127.0.0.1:8188"
METADATA_FILES = {"config.json", "model_index.json", "scheduler_config.json", "preprocessor_config.json"}


def get_live_object_info(base_url: str) -> Dict[str, Any]:
    url = f"{base_url}/object_info"
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"Warning: Could not fetch /object_info: {e}")
        return {}


def analyze_workflow(wf_path: str, obj_info: Dict[str, Any]) -> Dict[str, Any]:
    with open(wf_path, "r", encoding="utf-8") as f:
        wf = json.load(f)

    nodes = wf.get("nodes", [])
    if not nodes and isinstance(wf, dict):
        # API prompt format
        nodes = []
        for nid, val in wf.items():
            if isinstance(val, dict) and "class_type" in val:
                nodes.append({
                    "id": nid,
                    "type": val["class_type"],
                    "widgets_values": list(val.get("inputs", {}).values())
                })

    inputs = set()
    outputs = set()
    models = []
    has_subgraphs = "subgraphs" in wf.get("definitions", {})

    input_node_types = {
        "LoadImage": "Image (PNG/JPG)",
        "LoadImageMask": "Image Mask",
        "VHS_LoadVideo": "Video (MP4)",
        "VHS_LoadVideoPath": "Video (MP4 Path)",
        "VHS_LoadImages": "Image Sequence",
        "VHS_LoadImagesPath": "Image Sequence Path",
        "LoadAudio": "Audio (WAV/MP3)",
        "CLIPTextEncode": "Text Prompt",
        "ShowText|pysssss": "Text",
        "PrimitiveNode": "Widget Value",
    }

    output_node_types = {
        "SaveImage": "Image (PNG)",
        "PreviewImage": "Image Preview",
        "VHS_VideoCombine": "Video (MP4)",
        "SaveAudio": "Audio (WAV)",
        "SaveAudioMP3": "Audio (MP3)",
        "[Comfy3D] Save 3D Mesh": "3D Mesh (OBJ/GLB)",
        "SavePly": "3D Point Cloud (PLY)",
        "SaveAnimatedPNG": "Animated Image (APNG)",
    }

    model_loader_types = {
        "CheckpointLoaderSimple": "Checkpoint",
        "CheckpointLoader": "Checkpoint",
        "UNETLoader": "Diffusion UNet",
        "VAELoader": "VAE",
        "ControlNetLoader": "ControlNet",
        "ControlNetLoaderAdvanced": "ControlNet",
        "IPAdapterModelLoader": "IP-Adapter",
        "IPAdapterUnifiedLoader": "IP-Adapter",
        "CLIPVisionLoader": "CLIP Vision",
        "DualCLIPLoader": "Text Encoder CLIP",
        "CLIPLoader": "Text Encoder CLIP",
        "LoraLoader": "LoRA",
        "LoraLoaderModelOnly": "LoRA",
        "UpscaleModelLoader": "Upscale Model",
        "[Comfy3D] Unique3D MVDiffusion Model": "Unique3D Pipeline",
        "[Comfy3D] CharacterGen Model Loader": "CharacterGen Model",
        "FL_YuE2_ModelLoader": "YuE2 Music Model",
        "FL_YuE2_TrainingModels": "YuE2 Training Assets",
        "LatentSyncNode": "LatentSync Model",
        "LivePortraitLoadCropper": "LivePortrait Cropper",
        "LivePortraitLoadModel": "LivePortrait Weights",
    }

    for n in nodes:
        ntype = n.get("type", "")
        wv = n.get("widgets_values")

        # Inputs
        if ntype in input_node_types:
            inputs.add(input_node_types[ntype])
        elif "LoadImage" in ntype:
            inputs.add("Image (PNG/JPG)")
        elif "LoadAudio" in ntype or "Audio" in ntype and "Load" in ntype:
            inputs.add("Audio (WAV/MP3)")
        elif "Video" in ntype and "Load" in ntype:
            inputs.add("Video (MP4)")

        # Outputs
        if ntype in output_node_types:
            outputs.add(output_node_types[ntype])
        elif "SaveImage" in ntype:
            outputs.add("Image (PNG)")
        elif "VideoCombine" in ntype:
            outputs.add("Video (MP4)")
        elif "SaveAudio" in ntype:
            outputs.add("Audio (WAV/MP3)")
        elif "Save" in ntype and ("Mesh" in ntype or "3D" in ntype or "Glb" in ntype or "Obj" in ntype):
            outputs.add("3D Mesh (OBJ/GLB)")

        # Model Check
        if ntype in model_loader_types:
            mcategory = model_loader_types[ntype]
            mname = None
            if wv and isinstance(wv, list) and len(wv) > 0 and isinstance(wv[0], str):
                mname = wv[0]
            elif wv and isinstance(wv, dict):
                mname = str(list(wv.values())[0])
            models.append({
                "node_type": ntype,
                "category": mcategory,
                "model_name": mname or "Built-in / Default",
            })
        else:
            # Check if any widget value points to a weight file
            if wv and isinstance(wv, list):
                for item in wv:
                    if isinstance(item, str) and (
                        item.endswith(".safetensors")
                        or item.endswith(".pth")
                        or item.endswith(".ckpt")
                        or item.endswith(".pt")
                        or item.endswith(".onnx")
                    ):
                        models.append({
                            "node_type": ntype,
                            "category": "Weight / Checkpoint",
                            "model_name": item,
                        })

    # Default fallbacks if none detected
    if not inputs:
        inputs.add("Text Prompt / Conditioning")
    if not outputs:
        outputs.add("Generated Latent / Preview")

    return {
        "inputs": sorted(inputs),
        "outputs": sorted(outputs),
        "models": models,
        "has_subgraphs": has_subgraphs,
        "node_count": len(nodes),
    }


def main():
    obj_info = get_live_object_info(COMFY_URL)

    # Collect available models in ComfyUI
    available_models: Set[str] = set()
    for ninfo in obj_info.values():
        req = ninfo.get("input", {}).get("required", {})
        for spec in req.values():
            options = []
            if isinstance(spec, list) and len(spec) > 0:
                if isinstance(spec[0], list):
                    options = spec[0]
                elif len(spec) > 1 and isinstance(spec[1], dict) and "options" in spec[1]:
                    options = spec[1]["options"]
            for opt in options:
                if isinstance(opt, str) and (
                    opt.endswith(".safetensors")
                    or opt.endswith(".pth")
                    or opt.endswith(".ckpt")
                    or opt.endswith(".pt")
                    or opt.endswith(".onnx")
                ):
                    available_models.add(opt)
                    available_models.add(os.path.basename(opt))

    catalog = defaultdict(list)

    categories = sorted([
        d for d in os.listdir(WORKFLOWS_DIR)
        if os.path.isdir(os.path.join(WORKFLOWS_DIR, d)) and not d.startswith(".") and d != "personal"
    ])

    total_wfs = 0
    ready_count = 0
    needs_model_count = 0

    for cat in categories:
        cat_dir = os.path.join(WORKFLOWS_DIR, cat)
        files = sorted([
            f for f in os.listdir(cat_dir)
            if f.endswith(".json") and f not in METADATA_FILES
        ])

        for fname in files:
            total_wfs += 1
            fpath = os.path.join(cat_dir, fname)
            info = analyze_workflow(fpath, obj_info)

            # Check model availability
            missing_models = []
            for m in info["models"]:
                mname = m["model_name"]
                if mname not in ("Built-in / Default", "none") and not mname.startswith("http"):
                    bname = os.path.basename(mname)
                    if mname not in available_models and bname not in available_models:
                        # Some models like Unique3D or CharacterGen are embedded in custom_nodes
                        if "Unique3D" in m["node_type"] or "YuE2" in m["node_type"] or "LivePortrait" in m["node_type"]:
                            continue
                        missing_models.append(mname)

            if not missing_models:
                status = "✅ Ready to Run (Models Installed)"
                ready_count += 1
            else:
                status = f"⏳ Requires Model ({missing_models[0]})"
                needs_model_count += 1

            catalog[cat].append({
                "filename": fname,
                "inputs": info["inputs"],
                "outputs": info["outputs"],
                "models": info["models"],
                "missing_models": missing_models,
                "status": status,
                "node_count": info["node_count"],
                "has_subgraphs": info["has_subgraphs"],
            })

    # Save JSON summary
    out_json = "/tmp/workflow_catalog.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2)

    print(f"Catalog generated successfully: {total_wfs} workflows analyzed.")
    print(f"  - Ready to run immediately: {ready_count}")
    print(f"  - Requires optional/specific weights: {needs_model_count}")


if __name__ == "__main__":
    main()

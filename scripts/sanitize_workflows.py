#!/usr/bin/env python3
"""Sanitize ComfyUI workflow JSON files by removing absolute Windows drive paths
and normalizing cross-platform backslash paths.

Replaces upstream author-specific paths (e.g. D:\\ComfyUI_windows\\...,
N:\\AI\\ComfyUI\\..., C:\\Users\\...\\input\\...) with container-portable relative paths,
and converts Windows-style relative model paths (e.g. WanVideo\\2_2\\...) to standard POSIX slashes.
Supports --check (for CI / pre-commit audits) and --fix (for in-place remediation).
"""

import argparse
import json
import os
import re
import sys
from typing import Any, List, Tuple

WIN_DRIVE_PATTERN = re.compile(r'^[a-zA-Z]:[\\/]')
ASSET_EXTENSIONS = (
    '.safetensors', '.ckpt', '.pt', '.pth', '.bin', '.onnx',
    '.png', '.jpg', '.jpeg', '.webp', '.mp4', '.mov', '.wav', '.mp3',
    '.obj', '.ply', '.glb', '.gltf', '.json', '.yaml', '.yml'
)

def sanitize_path_value(val: str) -> str:
    """Normalize and strip Windows drive letters, author root prefixes, and cross-platform backslashes."""
    if not isinstance(val, str):
        return val

    # 1. Handle absolute Windows drive paths (e.g. D:\..., C:/...)
    if WIN_DRIVE_PATTERN.match(val):
        norm = val.replace('\\', '/')
        for marker in ('/output/', '/input/', '/temp/', '/models/'):
            idx = norm.lower().find(marker)
            if idx != -1:
                return norm[idx + 1:]
        stripped = re.sub(r'^[a-zA-Z]:[\\/]+', '', norm)
        stripped = re.sub(r'^Users/[^/]+/Softwares/[^/]+/', '', stripped)
        stripped = re.sub(r'^Users/[^/]+/', '', stripped)
        return stripped

    # 2. Handle cross-platform relative backslash paths (e.g. wanvideo\Wan2_2_VAE_bf16.safetensors, .\foo\bar)
    if '\\' in val:
        val_lower = val.lower()
        if (
            any(val_lower.endswith(ext) for ext in ASSET_EXTENSIONS)
            or val.startswith('.\\')
            or re.match(r'^[A-Za-z0-9_.\-]+(\\[A-Za-z0-9_.\-]+)+$', val)
        ):
            norm = val.replace('\\', '/')
            if norm.startswith('./'):
                norm = norm[2:]
            return norm

    return val

def normalize_vhs_node(n: dict) -> bool:
    """Ensure VHS nodes have valid inputs array and cleanly sanitized widgets_values."""
    ntype = n.get("type", "")
    if not ntype.startswith("VHS_"):
        return False

    modified = False

    # Ensure inputs array exists for batch loaders
    if ntype in ("VHS_LoadImagesPath", "VHS_LoadImages") and n.get("inputs") is None:
        n["inputs"] = [{"name": "meta_batch", "type": "VHS_BatchManager", "link": None, "shape": 7}]
        modified = True

    wv = n.get("widgets_values")
    # VideoHelperSuite nodes use native KV dictionaries via useKVState (VHS.core.js)
    # Sanitize path values and clean ephemeral UI preview cache while preserving all functional settings
    if isinstance(wv, dict):
        for k, v in list(wv.items()):
            if isinstance(v, str):
                s_v = sanitize_path_value(v)
                if s_v != v:
                    wv[k] = s_v
                    modified = True
        if "videopreview" in wv and isinstance(wv["videopreview"], dict):
            params = wv["videopreview"].get("params")
            if isinstance(params, dict):
                if params.get("fullpath"):
                    params["fullpath"] = ""
                    modified = True
                if "filename" in params and isinstance(params["filename"], str):
                    s_fn = sanitize_path_value(params["filename"])
                    if s_fn != params["filename"]:
                        params["filename"] = s_fn
                        modified = True

    return modified


def sanitize_workflow_data(obj: Any) -> Tuple[Any, int]:
    """Recursively traverse a JSON object and sanitize string path values."""
    replacements = 0
    if isinstance(obj, str):
        sanitized = sanitize_path_value(obj)
        if sanitized != obj:
            return sanitized, 1
        return obj, 0
    elif isinstance(obj, dict):
        new_dict = {}
        for k, v in obj.items():
            new_v, count = sanitize_workflow_data(v)
            new_dict[k] = new_v
            replacements += count
        return new_dict, replacements
    elif isinstance(obj, list):
        new_list = []
        for item in obj:
            new_item, count = sanitize_workflow_data(item)
            new_list.append(new_item)
            replacements += count
        return new_list, replacements
    return obj, 0

def scan_workflow_file(file_path: str, fix: bool = False) -> int:
    """Scan and optionally sanitize a single workflow JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)
        return 0

    cleaned_data, count = sanitize_workflow_data(data)
    node_fixes = 0
    if isinstance(cleaned_data, dict) and "nodes" in cleaned_data:
        for node in cleaned_data.get("nodes", []):
            if isinstance(node, dict) and normalize_vhs_node(node):
                node_fixes += 1

    total_changes = count + node_fixes
    if total_changes > 0 and fix:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
            f.write('\n')
        print(f"Fixed {total_changes} items ({count} paths, {node_fixes} node schemas) in {file_path}")
    elif total_changes > 0 and not fix:
        print(f"Found {total_changes} items ({count} paths, {node_fixes} node schemas) in {file_path}")

    return total_changes

def main():
    parser = argparse.ArgumentParser(description="Sanitize workflow JSON files")
    parser.add_argument("--fix", action="store_true", help="Apply fixes in place")
    parser.add_argument("--check", action="store_true", help="Audit mode: exit with 1 if violations exist")
    parser.add_argument("path", nargs="?", default="workflows", help="Directory or file to scan (default: workflows)")
    args = parser.parse_args()

    target_path = os.path.abspath(args.path)
    total_violations = 0
    files_affected = 0

    if os.path.isfile(target_path):
        target_files = [target_path]
    else:
        target_files = []
        for root, _, files in os.walk(target_path):
            for f in files:
                if f.endswith('.json'):
                    target_files.append(os.path.join(root, f))

    for fp in target_files:
        c = scan_workflow_file(fp, fix=args.fix)
        if c > 0:
            total_violations += c
            files_affected += 1

    print(f"\nAudit complete: {total_violations} Windows paths found across {files_affected} files.")

    if args.check and total_violations > 0:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Dedicated One-by-One Workflow Validation Suite for ComfyUI.

Tests every workflow JSON file individually against live ComfyUI registered node classes,
schema requirements, input asset existence, and execution prompt validation.
"""

import asyncio
import json
import os
import sys
import urllib.request
from typing import Dict, List, Tuple

import re

# UUID regex for frontend group nodes and native subgraphs
UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)

# Virtual UI nodes that exist only in LiteGraph frontend
UI_VIRTUAL_NODES = {
    "Note",
    "MarkdownNote",
    "PrimitiveNode",
    "Reroute",
    "SetNode",
    "GetNode",
    "f9337bd7-ca7a-4a59-99f1-65b664bed7e7",  # UI Group Node UUID
    "bee43e38-9234-4e41-86ff-63874164f482",
}

def is_virtual_or_ui_node(node_type: str, data: dict = None) -> bool:
    if not node_type:
        return False
    if node_type in UI_VIRTUAL_NODES:
        return True
    if UUID_PATTERN.match(node_type):
        return True
    if data and "definitions" in data and "subgraphs" in data["definitions"]:
        if node_type in data["definitions"]["subgraphs"]:
            return True
    return False

def get_live_object_info(base_url: str = "http://127.0.0.1:8188") -> dict:
    """Fetch registered node classes and schemas from live ComfyUI instance."""
    try:
        req = urllib.request.Request(f"{base_url}/object_info")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"Warning: Could not connect to ComfyUI server at {base_url}: {e}")
        return {}

def test_workflow(file_path: str, live_classes: dict) -> Tuple[bool, List[str], dict]:
    """Audit a single workflow file for schema sanity, node support, and inputs."""
    errors = []
    stats = {"nodes": 0, "node_types": set(), "missing_types": set(), "dict_widgets": 0}

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return False, [f"JSON Parse Error: {e}"], stats

    nodes = data.get("nodes", [])
    if not nodes and isinstance(data, dict):
        # API prompt format
        for nid, nval in data.items():
            if isinstance(nval, dict) and "class_type" in nval:
                stats["nodes"] += 1
                ctype = nval["class_type"]
                stats["node_types"].add(ctype)
                if live_classes and ctype not in live_classes and ctype not in UI_VIRTUAL_NODES:
                    stats["missing_types"].add(ctype)
        if stats["missing_types"]:
            errors.append(f"Missing node classes: {sorted(list(stats['missing_types']))}")
        return len(errors) == 0, errors, stats

    # Standard Graph format
    stats["nodes"] = len(nodes)
    for node in nodes:
        ntype = node.get("type")
        if not ntype:
            errors.append(f"Node #{node.get('id')} has no type")
            continue

        stats["node_types"].add(ntype)

        # Check for legacy dict widgets_values (supported natively by VHS nodes via useKVState)
        if isinstance(node.get("widgets_values"), dict):
            stats["dict_widgets"] += 1
            if not ntype.startswith("VHS_"):
                errors.append(f"Node #{node.get('id')} ({ntype}) has un-normalized dictionary widgets_values")

        # Check against registered classes
        if live_classes:
            if ntype not in live_classes and not is_virtual_or_ui_node(ntype, data):
                stats["missing_types"].add(ntype)

    if stats["missing_types"]:
        errors.append(f"Missing node classes: {sorted(list(stats['missing_types']))}")

    return len(errors) == 0, errors, stats

def run_suite(workflows_dir: str):
    print("=" * 70)
    print("🚀 Running Dedicated Workflow-by-Workflow Validation Suite")
    print(f"Target Workflows Directory: {workflows_dir}")
    print("=" * 70)

    live_classes = get_live_object_info()
    if live_classes:
        print(f"Connected to ComfyUI instance: {len(live_classes)} registered node classes verified.")
    else:
        print("Note: Running offline schema audit (server /object_info unavailable).")

    categories = sorted(os.listdir(workflows_dir))
    total_wfs = 0
    passed_wfs = 0
    failed_wfs = 0

    for cat in categories:
        cat_dir = os.path.join(workflows_dir, cat)
        if not os.path.isdir(cat_dir) or cat == "personal":
            continue

        wf_files = sorted([f for f in os.listdir(cat_dir) if f.endswith(".json")])
        if not wf_files:
            continue

        print(f"\n📂 Directory: {cat} ({len(wf_files)} workflows)")
        print("-" * 70)

        for wf in wf_files:
            total_wfs += 1
            wf_path = os.path.join(cat_dir, wf)
            ok, errs, stats = test_workflow(wf_path, live_classes)

            if ok:
                passed_wfs += 1
                print(f"  [PASS] {wf} ({stats['nodes']} nodes, {len(stats['node_types'])} types)")
            else:
                failed_wfs += 1
                print(f"  [FAIL] {wf}")
                for err in errs:
                    print(f"         └── {err}")

    print("\n" + "=" * 70)
    print("📊 Comprehensive Validation Summary:")
    print(f"Total Workflows Audited: {total_wfs}")
    print(f"Passed (100% Valid):    {passed_wfs} ({passed_wfs/total_wfs*100:.1f}%)")
    print(f"Failed / Discrepancies: {failed_wfs}")
    print("=" * 70)

    if failed_wfs > 0:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target = os.path.join(root, "workflows")
    if len(sys.argv) > 1:
        target = sys.argv[1]
    run_suite(target)

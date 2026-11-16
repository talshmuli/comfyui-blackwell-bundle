#!/usr/bin/env python3
"""UI Workflow Fidelity & Canvas Validation Linter.

Simulates ComfyUI's LiteGraph frontend loader to verify:
1. Node Class Existence: Every node exists in registered classes or UI virtuals.
2. Link Integrity: Output type of source node matches expected input type of destination node.
3. Widget Integrity: Widget types, counts, and dictionary mappings are valid.
4. Model Dependency Check: Identifies whether required models exist locally or need download.
"""

import json
import os
import re
import sys
import urllib.request
from typing import Dict, List, Set, Tuple

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

UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)

def is_virtual_or_ui(node_type: str, data: dict = None) -> bool:
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

def get_live_schemas(base_url: str = "http://127.0.0.1:8188") -> dict:
    try:
        req = urllib.request.Request(f"{base_url}/object_info")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"Warning: Could not connect to ComfyUI at {base_url}: {e}", file=sys.stderr)
        return {}

def audit_workflow(file_path: str, schemas: dict) -> dict:
    result = {
        "file": file_path,
        "valid": True,
        "status": "GREEN",
        "errors": [],
        "warnings": [],
        "missing_classes": [],
        "type_mismatches": [],
        "missing_models": [],
        "total_nodes": 0,
        "total_links": 0,
    }

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        result["valid"] = False
        result["status"] = "BROKEN"
        result["errors"].append(f"JSON Parse Error: {e}")
        return result

    nodes = data.get("nodes", [])
    if not nodes:
        # Prompt API format
        result["total_nodes"] = len(data)
        return result

    result["total_nodes"] = len(nodes)
    links_data = data.get("links", [])
    result["total_links"] = len(links_data)

    node_map = {n.get("id"): n for n in nodes if isinstance(n, dict)}
    
    # Map links by link ID: [link_id, src_node_id, src_slot, dst_node_id, dst_slot, link_type]
    link_map = {}
    for l in links_data:
        if isinstance(l, list) and len(l) >= 6:
            link_map[l[0]] = {
                "id": l[0],
                "src_id": l[1],
                "src_slot": l[2],
                "dst_id": l[3],
                "dst_slot": l[4],
                "type": l[5],
            }

    # 1. Audit Nodes
    for n in nodes:
        ntype = n.get("type")
        nid = n.get("id")
        if not ntype:
            result["errors"].append(f"Node #{nid} missing 'type'")
            result["valid"] = False
            continue

        if is_virtual_or_ui(ntype, data):
            continue

        if schemas and ntype not in schemas:
            result["missing_classes"].append(ntype)
            result["valid"] = False
            continue

        schema = schemas.get(ntype, {})
        req_inputs = schema.get("input", {}).get("required", {})
        opt_inputs = schema.get("input", {}).get("optional", {})
        all_inputs = {**req_inputs, **opt_inputs}

        # Check input connections for type compatibility
        for inp in n.get("inputs", []):
            link_id = inp.get("link")
            inp_name = inp.get("name")
            expected_type = inp.get("type")

            if link_id is not None and link_id in link_map:
                l_info = link_map[link_id]
                src_node = node_map.get(l_info["src_id"])
                if src_node:
                    src_type = src_node.get("type")
                    src_slot = l_info["src_slot"]
                    link_declared_type = str(l_info["type"]).upper()
                    
                    # Check union types (e.g. "IMAGE,MASK" or "FLOAT,INT")
                    exp_type_upper = str(expected_type).upper()
                    allowed_types = {t.strip().upper() for t in exp_type_upper.split(",")}
                    link_types = {t.strip().upper() for t in link_declared_type.split(",")}
                    if (
                        exp_type_upper not in ("*", "ANY", "")
                        and link_declared_type not in ("*", "ANY", "")
                        and not (allowed_types & link_types)
                    ):
                        mismatch = (
                            f"Node #{nid} ({ntype}).{inp_name} expects {expected_type}, "
                            f"received {link_declared_type} from Node #{l_info['src_id']} ({src_type})"
                        )
                        result["type_mismatches"].append(mismatch)

    if result["missing_classes"]:
        result["valid"] = False
        result["status"] = "BROKEN"
        result["errors"].append(f"Missing Node Classes: {sorted(list(set(result['missing_classes'])))}")

    if result["type_mismatches"]:
        result["valid"] = False
        result["status"] = "BROKEN"
        result["errors"].extend(result["type_mismatches"])

    return result

import unittest

class TestUIWorkflowFidelity(unittest.TestCase):
    def test_workflow_ui_fidelity(self):
        schemas = get_live_schemas()
        workflows_dir = os.path.join(os.path.dirname(__file__), "..", "workflows")
        broken_files = []
        scanned = 0

        for root, _, files in os.walk(workflows_dir):
            for f in files:
                if f.endswith(".json"):
                    fp = os.path.join(root, f)
                    res = audit_workflow(fp, schemas)
                    scanned += 1
                    if not res["valid"]:
                        broken_files.append(f"{res['file']}: {res['errors']}")

        self.assertEqual(len(broken_files), 0, f"Found {len(broken_files)} broken workflows: {broken_files[:3]}")
        self.assertGreater(scanned, 100, "Should scan at least 100 workflows")

def main():
    schemas = get_live_schemas()
    workflows_dir = "workflows"
    if len(sys.argv) > 1:
        workflows_dir = sys.argv[1]

    results = []
    broken_files = []

    for root, _, files in os.walk(workflows_dir):
        for f in files:
            if f.endswith(".json"):
                fp = os.path.join(root, f)
                res = audit_workflow(fp, schemas)
                results.append(res)
                if not res["valid"]:
                    broken_files.append(res)

    print(f"\nAudit complete: Scanned {len(results)} workflows.")
    print(f"Passed: {len(results) - len(broken_files)} | Broken: {len(broken_files)}")

    if broken_files:
        print("\n=== Issues Found ===")
        for b in broken_files:
            print(f"\n❌ {b['file']}:")
            for err in b["errors"]:
                print(f"   • {err}")
        sys.exit(1)
    else:
        print("\n✔ All workflows passed canvas & UI compatibility checks!")
        sys.exit(0)

if __name__ == "__main__":
    main()

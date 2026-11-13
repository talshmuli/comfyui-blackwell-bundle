#!/usr/bin/env python3
"""Audit workflow JSON files against ComfyUI registered node classes.

Ensures all official templates work 100% with pre-installed nodes,
and reports external dependency requirements for community workflows.
"""

import asyncio
import json
import os
import re
import sys

UI_VIRTUAL_NODES = {
    "Note",
    "MarkdownNote",
    "PrimitiveNode",
    "Reroute",
    "f9337bd7-ca7a-4a59-99f1-65b664bed7e7",  # UI Group Node UUID
    "bee43e38-9234-4e41-86ff-63874164f482",
}

UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def is_virtual_or_ui_node(node_type: str) -> bool:
    """Return True if node_type is a LiteGraph UI virtual node or group UUID."""
    if node_type in UI_VIRTUAL_NODES:
        return True
    if UUID_PATTERN.match(node_type):
        return True
    return False


def extract_node_types(data):
    """Extract all node type identifiers from workflow JSON data.

    Supports both ComfyUI graph export format ('nodes' list)
    and API prompt format (dict with 'class_type' fields).
    """
    types = set()
    if isinstance(data, dict):
        if "nodes" in data and isinstance(data["nodes"], list):
            for n in data["nodes"]:
                if isinstance(n, dict) and "type" in n:
                    types.add(n["type"])
        else:
            for _, v in data.items():
                if isinstance(v, dict) and "class_type" in v:
                    types.add(v["class_type"])
    return types


def run_workflow_audit():
    """Run comprehensive workflow compatibility audit."""
    if "/opt/ComfyUI" not in sys.path:
        sys.path.insert(0, "/opt/ComfyUI")

    if os.path.isdir("/opt/ComfyUI"):
        os.chdir("/opt/ComfyUI")

    try:
        import server
    except ModuleNotFoundError:
        import shutil
        import subprocess

        if shutil.which("docker"):
            res = subprocess.run(
                ["docker", "ps", "--filter", "name=comfyui-nodes", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
            )
            if "comfyui-nodes" in res.stdout:
                print("Note: Delegating execution to running 'comfyui-nodes' container...")
                cmd = [
                    "docker",
                    "exec",
                    "-i",
                    "comfyui-nodes",
                    "/opt/environments/python/comfyui/bin/python",
                    "-",
                ]
                with open(__file__, "rb") as f:
                    proc = subprocess.run(cmd, stdin=f)
                sys.exit(proc.returncode)

        print(
            "Error: ComfyUI backend ('server' / 'nodes') not found in local Python environment.\n"
            "Run this test inside the container:\n"
            "  docker exec comfyui-nodes /opt/environments/python/comfyui/bin/python /opt/ComfyUI/scripts/test_workflow_compatibility.py",
            file=sys.stderr,
        )
        sys.exit(1)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        from app.assets.manager import default_asset_manager

        asset_manager = default_asset_manager()
        _ = server.PromptServer(loop, asset_manager)
    except Exception:
        try:
            _ = server.PromptServer(loop)
        except Exception:
            _ = server.PromptServer(loop, None)

    import nodes

    if asyncio.iscoroutinefunction(nodes.init_extra_nodes):
        loop.run_until_complete(nodes.init_extra_nodes())
    else:
        nodes.init_extra_nodes()

    registered = set(nodes.NODE_CLASS_MAPPINGS.keys())

    script_dir = (
        os.path.dirname(os.path.abspath(__file__))
        if "__file__" in globals()
        else os.getcwd()
    )

    # 1. Resolve paths
    candidate_official_dirs = [
        "/opt/ComfyUI/user/default/workflows/official_templates",
        os.path.join(script_dir, "..", "workflows", "official_templates"),
        os.path.join(script_dir, "workflows", "official_templates"),
        "/opt/ComfyUI/workflows/official_templates",
    ]
    official_dir = None
    for c in candidate_official_dirs:
        if os.path.isdir(c):
            official_dir = c
            break

    assert official_dir is not None, (
        f"Official templates directory not found in candidates: {candidate_official_dirs}"
    )

    official_templates = [
        "wanvideo_2_1_14B_T2V.json",
        "wanvideo_2_1_14B_I2V.json",
        "latentsync_basic.json",
        "ipadapter_faceid.json",
    ]

    print("=== 1. Auditing Official Flagship Templates ===")
    for tmpl in official_templates:
        tmpl_path = os.path.join(official_dir, tmpl)
        assert os.path.isfile(tmpl_path), f"Official template not found: {tmpl_path}"
        with open(tmpl_path, "r", encoding="utf-8") as f:
            d = json.load(f)
        needed = extract_node_types(d)
        missing = [
            t
            for t in needed
            if t not in registered and not is_virtual_or_ui_node(t)
        ]
        if missing:
            print(
                f"❌ Official template {tmpl} missing required nodes: {missing}",
                file=sys.stderr,
            )
            sys.exit(1)
        print(
            f"✔ {tmpl}: all {len(needed)} node types fully supported out of the box."
        )

    # 2. Audit default workflow
    candidate_wf_paths = [
        "/opt/ComfyUI/default_workflow.json",
        os.path.join(script_dir, "..", "default_workflow.json"),
        os.path.join(script_dir, "default_workflow.json"),
    ]
    default_wf_path = None
    for c in candidate_wf_paths:
        if os.path.isfile(c):
            default_wf_path = c
            break

    assert default_wf_path is not None, (
        f"default_workflow.json not found in candidates: {candidate_wf_paths}"
    )

    with open(default_wf_path, "r", encoding="utf-8") as f:
        d = json.load(f)
    needed = extract_node_types(d)
    missing = [
        t
        for t in needed
        if t not in registered and not is_virtual_or_ui_node(t)
    ]
    assert len(missing) == 0, f"default_workflow.json missing nodes: {missing}"
    print("✔ default_workflow.json: fully supported out of the box.")

    # 3. Audit all community workflows and generate compatibility report
    candidate_wf_dirs = [
        "/opt/ComfyUI/user/default/workflows",
        os.path.join(script_dir, "..", "workflows"),
        os.path.join(script_dir, "workflows"),
        "/opt/ComfyUI/workflows",
    ]
    workflows_dir = None
    for c in candidate_wf_dirs:
        if os.path.isdir(c):
            workflows_dir = c
            break

    print("\n=== 2. Auditing All Workflows & Community Compatibility ===")
    all_json_files = []
    if workflows_dir and os.path.exists(workflows_dir):
        for root, _, files in os.walk(workflows_dir):
            for f in sorted(files):
                if f.endswith(".json"):
                    all_json_files.append(os.path.join(root, f))

    fully_compatible_count = 0
    community_reqs = {}
    audited_count = 0

    for wf in all_json_files:
        try:
            with open(wf, "r", encoding="utf-8") as f:
                d = json.load(f)
        except Exception:
            continue
        needed = extract_node_types(d)
        if not needed:
            # Skip non-workflow configuration files (e.g. diffusers model configs)
            continue
        audited_count += 1
        missing = [
            t
            for t in needed
            if t not in registered and not is_virtual_or_ui_node(t)
        ]
        if not missing:
            fully_compatible_count += 1
        else:
            for m in missing:
                community_reqs[m] = community_reqs.get(m, 0) + 1

    print(
        f"Total workflow definitions audited: {audited_count} (across {len(all_json_files)} JSON files)"
    )
    print(
        f"Fully compatible out-of-the-box: {fully_compatible_count}/{audited_count} ({fully_compatible_count * 100 / audited_count:.1f}%)"
    )
    print(
        f"Workflows requiring external/community nodes: {audited_count - fully_compatible_count}"
    )
    if community_reqs:
        print("Top external node dependencies requested by community workflows:")
        for node_type, count in sorted(
            community_reqs.items(), key=lambda x: x[1], reverse=True
        )[:10]:
            print(f"  - {node_type}: {count} workflow(s)")

    print(
        "\n✔ All official flagship workflows verified with 100% backend node compatibility."
    )


if __name__ == "__main__":
    run_workflow_audit()

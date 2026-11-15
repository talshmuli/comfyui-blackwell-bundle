#!/usr/bin/env python3
"""Comprehensive Workflow Validation & Local Execution Scanner for ComfyUI.

Iterates over every workflow template in workflows/, translates the UI graph to
an execution-ready prompt, validates inputs/models against the live ComfyUI
instance, and optionally executes workflows end-to-end to verify zero runtime errors.
"""

import argparse
import copy
import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

METADATA_FILES = {
    "config.json",
    "model_index.json",
    "scheduler_config.json",
    "preprocessor_config.json",
}


def get_live_object_info(base_url: str) -> Dict[str, Any]:
    url = f"{base_url}/object_info"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def interrupt_and_clear_queue(base_url: str) -> None:
    try:
        req_int = urllib.request.Request(f"{base_url}/interrupt", data=b"", headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req_int, timeout=5)
    except Exception:
        pass
    try:
        req_clr = urllib.request.Request(
            f"{base_url}/queue",
            data=json.dumps({"clear": True}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req_clr, timeout=5)
    except Exception:
        pass


def is_widget_type(spec: Any) -> bool:
    if not spec:
        return False
    itype = spec[0] if isinstance(spec, (list, tuple)) else spec
    if isinstance(itype, list):
        return True
    if itype in (
        "INT",
        "FLOAT",
        "STRING",
        "BOOLEAN",
        "COMBO",
        "INT:seed",
        "NUMBER",
        "COMFY_DYNAMICCOMBO_V3",
    ):
        return True
    return False


def flatten_subgraphs(wf: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(wf, dict) or "definitions" not in wf or "subgraphs" not in wf.get("definitions", {}):
        return wf

    wf = copy.deepcopy(wf)
    subgraph_map = {
        sg["id"]: sg
        for sg in wf["definitions"]["subgraphs"]
        if isinstance(sg, dict) and "id" in sg
    }

    links_dict = {}
    for l in wf.get("links", []):
        if not l:
            continue
        if isinstance(l, (list, tuple)) and len(l) >= 6:
            links_dict[l[0]] = {
                "id": l[0],
                "origin_id": l[1],
                "origin_slot": l[2],
                "target_id": l[3],
                "target_slot": l[4],
                "type": l[5],
            }
        elif isinstance(l, dict):
            lid = l.get("id", l.get(0, l.get("0")))
            if lid is not None:
                links_dict[lid] = {
                    "id": lid,
                    "origin_id": l.get("origin_id", l.get(1, l.get("1"))),
                    "origin_slot": l.get("origin_slot", l.get(2, l.get("2"))),
                    "target_id": l.get("target_id", l.get(3, l.get("3"))),
                    "target_slot": l.get("target_slot", l.get(4, l.get("4"))),
                    "type": l.get("type", l.get(5, l.get("5"))),
                }

    next_link_id = max((k for k in links_dict.keys() if isinstance(k, int)), default=100000) + 1

    changed = True
    iterations = 0
    while changed and iterations < 20:
        iterations += 1
        changed = False
        nodes = wf.get("nodes", [])
        new_nodes = []
        for n in nodes:
            ntype = n.get("type")
            if ntype not in subgraph_map:
                new_nodes.append(n)
                continue

            changed = True
            inst_id = n.get("id")
            sg = subgraph_map[ntype]
            in_node_id = sg.get("inputNode", {}).get("id", -10)
            out_node_id = sg.get("outputNode", {}).get("id", -20)

            inst_inputs_by_name = {
                inp.get("name"): inp for inp in n.get("inputs", []) if inp.get("name")
            }
            sg_inputs = sg.get("inputs", [])
            sg_outputs = sg.get("outputs", [])

            inst_inner_nodes = []
            for inner in sg.get("nodes", []):
                inner_copy = copy.deepcopy(inner)
                inner_copy["id"] = f"{inst_id}:{inner['id']}"
                inst_inner_nodes.append(inner_copy)

            inner_nodes_by_id = {inner["id"]: inner for inner in inst_inner_nodes}

            for sl in sg.get("links", []):
                if not isinstance(sl, dict):
                    continue
                orig_id = sl.get("origin_id")
                orig_slot = sl.get("origin_slot")
                tgt_id = sl.get("target_id")
                tgt_slot = sl.get("target_slot")
                ltype = sl.get("type")

                if orig_id == in_node_id:
                    sg_inp = sg_inputs[orig_slot] if orig_slot < len(sg_inputs) else None
                    if sg_inp:
                        inst_inp = inst_inputs_by_name.get(sg_inp.get("name"))
                        if inst_inp and inst_inp.get("link") is not None:
                            ext_link = links_dict.get(inst_inp["link"])
                            if ext_link:
                                nl_id = next_link_id
                                next_link_id += 1
                                links_dict[nl_id] = {
                                    "id": nl_id,
                                    "origin_id": ext_link["origin_id"],
                                    "origin_slot": ext_link["origin_slot"],
                                    "target_id": f"{inst_id}:{tgt_id}",
                                    "target_slot": tgt_slot,
                                    "type": ltype,
                                }
                                tgt_node = inner_nodes_by_id.get(f"{inst_id}:{tgt_id}")
                                if tgt_node and "inputs" in tgt_node:
                                    for t_inp in tgt_node["inputs"]:
                                        if t_inp.get("link") == sl.get("id"):
                                            t_inp["link"] = nl_id
                                            break
                elif tgt_id == out_node_id:
                    outp_slot_idx = tgt_slot
                    for olid, ol in list(links_dict.items()):
                        if str(ol["origin_id"]) == str(inst_id) and ol["origin_slot"] == outp_slot_idx:
                            ol["origin_id"] = f"{inst_id}:{orig_id}"
                            ol["origin_slot"] = orig_slot
                else:
                    nl_id = next_link_id
                    next_link_id += 1
                    links_dict[nl_id] = {
                        "id": nl_id,
                        "origin_id": f"{inst_id}:{orig_id}",
                        "origin_slot": orig_slot,
                        "target_id": f"{inst_id}:{tgt_id}",
                        "target_slot": tgt_slot,
                        "type": ltype,
                    }
                    tgt_node = inner_nodes_by_id.get(f"{inst_id}:{tgt_id}")
                    if tgt_node and "inputs" in tgt_node:
                        for t_inp in tgt_node["inputs"]:
                            if t_inp.get("link") == sl.get("id"):
                                t_inp["link"] = nl_id
                                break

            new_nodes.extend(inst_inner_nodes)
        wf["nodes"] = new_nodes
        wf["links"] = list(links_dict.values())

    return wf


def workflow_graph_to_prompt(wf: Dict[str, Any], obj_info: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    warnings = []
    nodes = wf.get("nodes", [])

    # If already in prompt format
    if not nodes and isinstance(wf, dict):
        is_prompt = any(isinstance(v, dict) and "class_type" in v for v in wf.values())
        if is_prompt:
            return wf, warnings

    if isinstance(wf, dict) and "definitions" in wf and "subgraphs" in wf.get("definitions", {}):
        wf = flatten_subgraphs(wf)
        nodes = wf.get("nodes", [])

    links_by_id = {}
    for link in wf.get("links", []):
        if not link:
            continue
        if isinstance(link, (list, tuple)) and len(link) >= 3:
            links_by_id[link[0]] = (link[0], link[1], link[2])
        elif isinstance(link, dict):
            lid = link.get(0, link.get("0", link.get("id")))
            origin_id = link.get(1, link.get("1", link.get("origin_id")))
            origin_slot = link.get(2, link.get("2", link.get("origin_slot")))
            if lid is not None:
                links_by_id[lid] = (lid, origin_id, origin_slot)

    nodes_by_id = {node["id"]: node for node in nodes if "id" in node}

    def resolve_link(link_id: int, visited: Optional[set] = None) -> Any:
        if visited is None:
            visited = set()
        if link_id in visited or link_id not in links_by_id:
            return None
        visited.add(link_id)

        lnk = links_by_id[link_id]
        origin_id, origin_slot = lnk[1], lnk[2]
        origin_node = nodes_by_id.get(origin_id)
        if origin_node:
            ntype = origin_node.get("type")
            if ntype == "Reroute":
                rinp = origin_node.get("inputs", [])
                if rinp and rinp[0].get("link") is not None:
                    return resolve_link(rinp[0]["link"], visited)
            elif ntype == "PrimitiveNode":
                rinp = origin_node.get("inputs", [])
                if rinp and rinp[0].get("link") is not None:
                    return resolve_link(rinp[0]["link"], visited)
                wv = origin_node.get("widgets_values")
                if wv:
                    return wv[0]
        return [str(origin_id), origin_slot]

    prompt: Dict[str, Any] = {}

    for node in nodes:
        nid = str(node.get("id"))
        ntype = node.get("type")
        if not ntype or ntype in ("Note", "MarkdownNote", "PrimitiveNode", "Reroute"):
            continue

        if ntype not in obj_info:
            warnings.append(f"Node #{nid} has unmapped type: {ntype}")
            continue

        ninfo = obj_info[ntype]
        inp_info = ninfo.get("input", {})
        req = inp_info.get("required", {})
        opt = inp_info.get("optional", {})
        all_inputs = {}
        all_inputs.update(req)
        all_inputs.update(opt)

        input_order = ninfo.get("input_order", {})
        ordered_names = input_order.get("required", list(req.keys())) + input_order.get("optional", list(opt.keys()))

        widget_list = []
        for name in ordered_names:
            if name in all_inputs and is_widget_type(all_inputs[name]):
                widget_list.append(name)

        node_inputs: Dict[str, Any] = {}

        # 1. Connected slots
        for inp in node.get("inputs", []):
            slot_name = inp.get("name")
            link_id = inp.get("link")
            if link_id is not None and slot_name:
                resolved = resolve_link(link_id)
                if resolved is not None:
                    node_inputs[slot_name] = resolved

        # 2. Widgets
        wv = node.get("widgets_values")
        if wv is not None:
            if isinstance(wv, dict):
                for k, v in wv.items():
                    if k not in node_inputs and k in all_inputs:
                        node_inputs[k] = v
            elif isinstance(wv, list):
                w_idx = 0
                for wname in widget_list:
                    if w_idx >= len(wv):
                        break
                    val = wv[w_idx]
                    if wname not in node_inputs and wname in all_inputs:
                        node_inputs[wname] = val
                    w_idx += 1
                    # Skip control_after_generate token if present
                    if (
                        wname in ("seed", "noise_seed")
                        and w_idx < len(wv)
                        and isinstance(wv[w_idx], str)
                        and wv[w_idx] in ("fixed", "randomize", "increment", "decrement")
                    ):
                        w_idx += 1

        # 3. Fallback to schema defaults for any required inputs missing in legacy exports
        for wname in widget_list:
            if wname not in node_inputs and wname in req:
                spec = req[wname]
                if isinstance(spec, (list, tuple)) and len(spec) > 1 and isinstance(spec[1], dict) and "default" in spec[1]:
                    node_inputs[wname] = spec[1]["default"]
                elif isinstance(spec, (list, tuple)) and isinstance(spec[0], list) and len(spec[0]) > 0:
                    node_inputs[wname] = spec[0][0]

        prompt[nid] = {
            "class_type": ntype,
            "inputs": node_inputs,
        }

    return prompt, warnings


def test_prompt_validation(
    base_url: str, prompt: Dict[str, Any], execute: bool = False
) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    data = json.dumps({"prompt": prompt}).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url}/prompt", data=data, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            prompt_id = res.get("prompt_id")
            if not execute:
                interrupt_and_clear_queue(base_url)
            return True, prompt_id, None
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="ignore")
        try:
            err_json = json.loads(err_body)
        except Exception:
            err_json = {"raw": err_body}
        return False, None, err_json


def monitor_execution(base_url: str, prompt_id: str, timeout: int = 120) -> Tuple[bool, Optional[str]]:
    start_time = time.time()
    while time.time() - start_time < timeout:
        time.sleep(2)
        try:
            with urllib.request.urlopen(f"{base_url}/history/{prompt_id}", timeout=5) as resp:
                hist = json.loads(resp.read().decode("utf-8"))
                if prompt_id in hist:
                    entry = hist[prompt_id]
                    status = entry.get("status", {})
                    if status.get("completed", False):
                        return True, None
                    if status.get("status_str") == "error":
                        messages = status.get("messages", [])
                        err_msg = "Unknown execution error"
                        for m in messages:
                            if m[0] == "execution_error":
                                err_msg = m[1].get("exception_message", err_msg)
                        return False, err_msg
        except Exception:
            pass
    return False, "Execution timed out"


def scan_workflows(workflows_dir: str, base_url: str, execute_single: Optional[str] = None):
    print("=" * 80)
    print("🔍 ComfyUI Universal Workflow Scan & Live Validation Suite")
    print(f"Target Directory: {workflows_dir}")
    print(f"ComfyUI Server:   {base_url}")
    print("=" * 80)

    try:
        obj_info = get_live_object_info(base_url)
        print(f"✅ Connected to ComfyUI: {len(obj_info)} registered classes loaded.")
    except Exception as e:
        print(f"❌ Failed to connect to ComfyUI server at {base_url}: {e}")
        sys.exit(1)

    all_wfs = []
    for root, _, files in os.walk(workflows_dir):
        if "personal" in root:
            continue
        for f in sorted(files):
            if f.endswith(".json") and f not in METADATA_FILES:
                all_wfs.append(os.path.join(root, f))

    all_wfs.sort()
    print(f"Found {len(all_wfs)} public workflow templates to audit.\n")

    results = {"pass": 0, "fail": 0, "errors": {}}

    for wf_path in all_wfs:
        rel_path = os.path.relpath(wf_path, workflows_dir)
        wf_name = os.path.basename(wf_path)

        if execute_single and wf_name != execute_single and rel_path != execute_single:
            continue

        try:
            with open(wf_path, "r", encoding="utf-8") as f:
                wf_data = json.load(f)
        except Exception as e:
            print(f"❌ [PARSE FAIL] {rel_path}: {e}")
            results["fail"] += 1
            results["errors"][rel_path] = f"JSON Parse Error: {e}"
            continue

        prompt, warnings = workflow_graph_to_prompt(wf_data, obj_info)
        if not prompt:
            print(f"⚠️  [EMPTY PROMPT] {rel_path}")
            results["fail"] += 1
            results["errors"][rel_path] = "Empty or untranslatable prompt graph"
            continue

        valid, prompt_id, err_info = test_prompt_validation(
            base_url, prompt, execute=bool(execute_single)
        )

        if valid:
            if execute_single and prompt_id:
                print(f"⏳ Executing {rel_path} (ID: {prompt_id})...")
                ok, exec_err = monitor_execution(base_url, prompt_id)
                if ok:
                    print(f"✅ [EXECUTED: PASS] {rel_path}")
                    results["pass"] += 1
                else:
                    print(f"❌ [EXECUTE FAIL] {rel_path}: {exec_err}")
                    results["fail"] += 1
                    results["errors"][rel_path] = f"Execution error: {exec_err}"
            else:
                print(f"✅ [VALIDATED: PASS] {rel_path}")
                results["pass"] += 1
        else:
            print(f"❌ [VALIDATE FAIL] {rel_path}")
            summary = []
            if err_info and "node_errors" in err_info:
                for nid, nerr in err_info["node_errors"].items():
                    ctype = nerr.get("class_type", "Unknown")
                    for e in nerr.get("errors", []):
                        summary.append(f"Node #{nid} ({ctype}): {e.get('message')} - {e.get('details')}")
            err_str = "; ".join(summary) if summary else str(err_info)
            print(f"   └── {err_str}")
            results["fail"] += 1
            results["errors"][rel_path] = err_str

    print("\n" + "=" * 80)
    print("📊 Scan Summary Report:")
    print(f"Total Audited:  {results['pass'] + results['fail']}")
    print(f"Passed:          {results['pass']}")
    print(f"Failed:          {results['fail']}")
    print("=" * 80)

    if results["fail"] > 0:
        print("\nFailures Breakdown:")
        for path, err in sorted(results["errors"].items()):
            print(f"- {path}:\n  {err}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Universal ComfyUI Workflow Scanner")
    parser.add_argument("--url", default="http://127.0.0.1:8188", help="ComfyUI server URL")
    parser.add_argument(
        "--workflows",
        default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "workflows"),
        help="Path to workflows directory",
    )
    parser.add_argument("--execute", default=None, help="Specific workflow to execute end-to-end")
    args = parser.parse_args()

    scan_workflows(args.workflows, args.url, execute_single=args.execute)

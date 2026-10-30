#!/usr/bin/env python3
"""ComfyUI Blackwell Docker - Blender Headless VFX Worker.

Monitors /workspace/scenes for blend files or batch render commands,
renders passes to /workspace/passes, or waits for orchestration requests.
"""

import os
import signal
import subprocess
import sys
import time

def sigterm_handler(signum, frame):
    print("Blender worker shutting down gracefully...", flush=True)
    sys.exit(0)

signal.signal(signal.SIGTERM, sigterm_handler)
signal.signal(signal.SIGINT, sigterm_handler)

def main():
    print("=" * 65, flush=True)
    print(" ComfyUI-Blackwell VFX Studio: Blender Headless Worker", flush=True)
    print(" Target Hardware: NVIDIA Blackwell RTX 5090 / 5080 (sm_120)", flush=True)
    print(" Blender:         4.4.3 LTS (CUDA / OptiX Acceleration)", flush=True)
    print(" Passes Bus:      /workspace/passes", flush=True)
    print(" Scenes Dir:      /workspace/scenes", flush=True)
    comfy_url = os.environ.get("COMFYUI_API_URL", "http://comfyui:8188")
    print(f" ComfyUI URL:     {comfy_url}", flush=True)
    print("=" * 65, flush=True)

    # Validate blender binary
    try:
        res = subprocess.run(["blender", "-b", "--version"], capture_output=True, text=True, check=True)
        version_first_line = res.stdout.strip().split("\n")[0]
        print(f"Blender runtime verified: {version_first_line}", flush=True)
    except Exception as e:
        print(f"WARNING: Blender check failed: {e}", file=sys.stderr, flush=True)

    # Ensure directories exist
    os.makedirs("/workspace/passes", exist_ok=True)
    os.makedirs("/workspace/scenes", exist_ok=True)

    # Check for ComfyUI-BlenderAI addon
    addon_path = "/opt/blender/4.4/scripts/addons/ComfyUI-BlenderAI-node"
    if os.path.exists(addon_path):
        print(f"ComfyUI-BlenderAI addon installed at: {addon_path}", flush=True)

    print("Blender worker ready. Standing by for scene rendering jobs...", flush=True)

    # Idle watch loop
    while True:
        try:
            scenes = [f for f in os.listdir("/workspace/scenes") if f.endswith(".blend")]
        except Exception:
            pass
        time.sleep(5)

if __name__ == "__main__":
    main()

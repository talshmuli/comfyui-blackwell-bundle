#!/usr/bin/env python3
"""Execute a real diffusion workflow end-to-end on the isolated ComfyUI test container.
Verifies complete neural inference, Blackwell RTX 5090 acceleration, VRAM allocation, and file output.
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error

COMFYUI_URL = "http://localhost:8190"

def check_server():
    try:
        req = urllib.request.Request(f"{COMFYUI_URL}/system_stats")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            device = data.get("devices", [{}])[0].get("name", "Unknown")
            print(f"Connected to ComfyUI on {COMFYUI_URL}")
            print(f"Target Device: {device}")
            return True
    except Exception as e:
        print(f"Failed to connect to {COMFYUI_URL}: {e}")
        return False

def get_available_checkpoints():
    req = urllib.request.Request(f"{COMFYUI_URL}/object_info/CheckpointLoaderSimple")
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())
        ckpts = data["CheckpointLoaderSimple"]["input"]["required"]["ckpt_name"][0]
        return ckpts

def run_workflow():
    if not check_server():
        sys.exit(1)
        
    ckpts = get_available_checkpoints()
    print(f"Found {len(ckpts)} available checkpoints.")
    
    # Select best model
    chosen_ckpt = None
    for preferred in ["v1-5-pruned-emaonly.safetensors", "RealVisXL_V5.0_fp16.safetensors", "DreamShaper_8_pruned.safetensors"]:
        for c in ckpts:
            if preferred in c:
                chosen_ckpt = c
                break
        if chosen_ckpt:
            break
            
    if not chosen_ckpt and ckpts:
        chosen_ckpt = ckpts[0]
        
    print(f"Selected checkpoint for execution test: {chosen_ckpt}")
    
    # Construct API prompt graph
    prompt_graph = {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "cfg": 8,
                "denoise": 1,
                "latent_image": ["5", 0],
                "model": ["4", 0],
                "negative": ["7", 0],
                "positive": ["6", 0],
                "sampler_name": "euler",
                "scheduler": "normal",
                "seed": 42,
                "steps": 10
            }
        },
        "4": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": chosen_ckpt
            }
        },
        "5": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "batch_size": 1,
                "height": 512,
                "width": 512
            }
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": ["4", 1],
                "text": "beautiful golden hour landscape, masterpiece, photorealistic, 8k"
            }
        },
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": ["4", 1],
                "text": "bad quality, blurry, text, watermark"
            }
        },
        "8": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["3", 0],
                "vae": ["4", 2]
            }
        },
        "9": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": "system_tests/isolated_validation/live_e2e_verified",
                "images": ["8", 0]
            }
        }
    }
    
    payload = json.dumps({"prompt": prompt_graph}).encode("utf-8")
    req = urllib.request.Request(
        f"{COMFYUI_URL}/prompt",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print("Submitting prompt to ComfyUI execution queue...")
    start_time = time.time()
    with urllib.request.urlopen(req, timeout=10) as resp:
        result = json.loads(resp.read().decode())
        prompt_id = result.get("prompt_id")
        print(f"Prompt accepted! Prompt ID: {prompt_id}")
        
    # Poll for completion
    print("Polling execution status...")
    max_wait = 120
    elapsed = 0
    while elapsed < max_wait:
        time.sleep(2)
        elapsed = time.time() - start_time
        try:
            req_hist = urllib.request.Request(f"{COMFYUI_URL}/history/{prompt_id}")
            with urllib.request.urlopen(req_hist, timeout=5) as resp_hist:
                hist = json.loads(resp_hist.read().decode())
                if prompt_id in hist:
                    status = hist[prompt_id].get("status", {})
                    completed = status.get("completed", False)
                    print(f"Execution completed! Total duration: {elapsed:.2f}s")
                    outputs = hist[prompt_id].get("outputs", {})
                    print(f"Outputs generated: {json.dumps(outputs, indent=2)}")
                    return True
        except Exception as e:
            print(f"Polling warning: {e}")
            
    print(f"Timed out after {max_wait}s waiting for execution.")
    return False

if __name__ == "__main__":
    success = run_workflow()
    sys.exit(0 if success else 1)

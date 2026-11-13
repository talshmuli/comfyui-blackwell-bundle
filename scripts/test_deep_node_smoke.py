#!/usr/bin/env python3
"""Deep local smoke test verifying all newly added and patched custom nodes.

Instantiates representative node classes directly, performs functional execution
smoke tests on key node operations, and asserts zero import failures.
"""

import asyncio
import importlib
import os
import sys


def run_deep_smoke():
    # Setup ComfyUI paths
    if "/opt/ComfyUI" not in sys.path:
        sys.path.insert(0, "/opt/ComfyUI")
    os.chdir("/opt/ComfyUI")

    import server

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        from app.assets.manager import default_asset_manager
        asset_manager = default_asset_manager()
        s = server.PromptServer(loop, asset_manager)
    except Exception:
        try:
            s = server.PromptServer(loop)
        except Exception:
            s = server.PromptServer(loop, None)

    import nodes
    if asyncio.iscoroutinefunction(nodes.init_extra_nodes):
        loop.run_until_complete(nodes.init_extra_nodes())
    else:
        nodes.init_extra_nodes()

    # 1. Assert zero custom node import failures
    failed_nodes = getattr(nodes, "failed_nodes", [])
    if failed_nodes:
        print(f"❌ Custom node import failures detected: {failed_nodes}", file=sys.stderr)
        sys.exit(1)
    print(f"✔ Zero custom node import failures verified across {len(nodes.NODE_CLASS_MAPPINGS)} registered nodes.")

    # 2. Key representative node classes to instantiate (5 new, 7 patched, 2 utilities = 19 classes)
    target_node_classes = [
        # Newly added nodes:
        ("ComfyUI-Crystools", "Primitive boolean [Crystools]"),
        ("ComfyUI-MelBandRoFormer", "MelBandRoFormerModelLoader"),
        ("ComfyUI-MelBandRoFormer", "MelBandRoFormerSampler"),
        ("ComfyUI_FL-HeartMuLa", "FL_HeartMuLa_ModelLoader"),
        ("ComfyUI_FL-HeartMuLa", "FL_HeartMuLa_Sampler"),
        ("ACE-Step-ComfyUI", "AceStepSettings"),
        ("ACE-Step-ComfyUI", "AceStepAudioCodes"),
        ("ComfyUI-Step1X-Edit", "Step1X_LoadAEModel"),
        ("ComfyUI-Step1X-Edit", "Step1X_Prompt"),

        # Patched nodes:
        ("ComfyUI-WanVideoWrapper", "WanVideoModelLoader"),
        ("ComfyUI-WanVideoWrapper", "WanVideoSampler"),
        ("ComfyUI-LTXVideo", "LTXVImgToVideoAdvanced"),
        ("ComfyUI-LivePortraitKJ", "DownloadAndLoadLivePortraitModels"),
        ("ComfyUI-3D-Pack", "Load3D"),
        ("ComfyUI-VideoHelperSuite", "VHS_VideoCombine"),
        ("ComfyUI-FL-YuE2", "FL_YuE2_ModelLoader"),
        ("ComfyUI-RVC", "RVC_Infer"),

        # Pre-installed utilities:
        ("ComfyUI-KJNodes", "ColorMatch"),
        ("ComfyUI_IPAdapter_plus", "IPAdapterModelLoader")
    ]

    print(f"\n=== Step 1: Instantiating {len(target_node_classes)} Key Node Classes ===")
    instantiated = 0
    for repo, cls_name in target_node_classes:
        cls = nodes.NODE_CLASS_MAPPINGS.get(cls_name)
        if cls is None:
            print(f"❌ Missing mapping for {cls_name} ({repo})", file=sys.stderr)
            sys.exit(1)
        try:
            _ = cls()
            instantiated += 1
            print(f"✔ Instantiated {cls_name} ({repo})")
        except Exception as e:
            print(f"❌ Failed instantiating {cls_name} ({repo}): {e}", file=sys.stderr)
            sys.exit(1)

    print(f"✔ All {instantiated}/{len(target_node_classes)} key node classes instantiated cleanly.")

    # 3. Functional Execution Tests
    print("\n=== Step 2: Functional Execution Tests ===")

    # 3a. ComfyUI-Crystools: Hardware monitoring & GPU detection
    try:
        crystools_gpu = importlib.import_module("custom_nodes.ComfyUI-Crystools.general.gpu")
        gpu_info = crystools_gpu.CGPUInfo()
        info = gpu_info.getInfo()
        status = gpu_info.getStatus()
        assert isinstance(status, dict) and "gpus" in status, "Crystools getStatus returned invalid payload"
        gpus = status.get("gpus", [])
        assert len(gpus) > 0, "Crystools failed to detect any GPU devices via pynvml"
        gpu_name = info[0]["name"] if info and isinstance(info, list) and "name" in info[0] else "NVIDIA GPU"
        vram_gb = gpus[0]["vram_total"] // (1024 ** 3)
        temp_c = gpus[0]["gpu_temperature"]
        print(f"✔ ComfyUI-Crystools functional test passed: {gpu_name} (VRAM: {vram_gb} GB, temp: {temp_c}°C)")
    except Exception as e:
        print(f"❌ ComfyUI-Crystools functional test failed: {e}", file=sys.stderr)
        sys.exit(1)

    # 3b. ACE-Step-ComfyUI: Invoke AceStepSettings execution method
    try:
        ace_cls = nodes.NODE_CLASS_MAPPINGS["AceStepSettings"]
        ace_inst = ace_cls()
        settings_res = ace_inst.build(
            seed="42",
            thinking=True,
            use_cot_caption=True,
            use_cot_language=True,
            temperature=0.85,
            lm_cfg_scale=2.0,
            lm_top_p=0.9,
            lm_top_k=0,
            dit_guidance_scale=7.0,
            dit_inference_steps=8,
            dit_infer_method="ode"
        )
        assert isinstance(settings_res, tuple) and len(settings_res) == 1, "AceStepSettings build return format mismatch"
        assert settings_res[0].get("seed") == "42", "AceStepSettings returned incorrect seed"
        assert settings_res[0].get("dit_infer_method") == "ode", "AceStepSettings returned incorrect infer_method"
        print("✔ ACE-Step-ComfyUI functional test passed: AceStepSettings.build() produced valid settings")
    except Exception as e:
        print(f"❌ ACE-Step-ComfyUI functional test failed: {e}", file=sys.stderr)
        sys.exit(1)

    # 3c. ComfyUI-Step1X-Edit: Invoke Step1X_Prompt execution method
    try:
        step1x_cls = nodes.NODE_CLASS_MAPPINGS["Step1X_Prompt"]
        step1x_inst = step1x_cls()
        test_prompt = "A high-tech Blackwell datacenter running local AI workflows"
        prompt_res = step1x_inst.input_prompt(prompt=test_prompt)
        assert isinstance(prompt_res, tuple) and len(prompt_res) == 1, "Step1X_Prompt input_prompt return format mismatch"
        assert prompt_res[0] == test_prompt, "Step1X_Prompt returned unexpected prompt text"
        print("✔ ComfyUI-Step1X-Edit functional test passed: Step1X_Prompt.input_prompt() validated")
    except Exception as e:
        print(f"❌ ComfyUI-Step1X-Edit functional test failed: {e}", file=sys.stderr)
        sys.exit(1)

    # 3d. ComfyUI-VideoHelperSuite: Invoke VHS_VideoCombine validation logic
    try:
        vhs_cls = nodes.NODE_CLASS_MAPPINGS["VHS_VideoCombine"]
        vhs_types = vhs_cls.INPUT_TYPES()
        assert "required" in vhs_types and "format" in vhs_types["required"], "VHS_VideoCombine INPUT_TYPES missing format specification"
        formats = vhs_types["required"]["format"][0]
        assert "image/gif" in formats, "VHS_VideoCombine formats missing image/gif standard format"
        vhs_inst = vhs_cls()
        combine_res = vhs_inst.combine_video(
            frame_rate=8,
            loop_count=0,
            images=None,
            save_output=False
        )
        assert combine_res == ((False, []),), f"Unexpected combine_video empty fallback: {combine_res}"
        print(f"✔ ComfyUI-VideoHelperSuite functional test passed: VHS_VideoCombine validated {len(formats)} formats and safe execution")
    except Exception as e:
        print(f"❌ ComfyUI-VideoHelperSuite functional test failed: {e}", file=sys.stderr)
        sys.exit(1)

    # 4. CUDA sm_120 compute & torch.compile test
    print("\n=== Step 3: CUDA sm_120 Compute & torch.compile Tests ===")
    import torch
    if torch.cuda.is_available():
        device_name = torch.cuda.get_device_name(0)
        print(f"CUDA Device: {device_name}")

        # sm_120 FP16 matmul
        a = torch.randn(512, 512, device="cuda", dtype=torch.float16)
        b = torch.randn(512, 512, device="cuda", dtype=torch.float16)
        c = torch.matmul(a, b)
        assert c.shape == (512, 512), "CUDA matmul returned incorrect shape"
        del a, b, c
        torch.cuda.empty_cache()
        print("✔ CUDA sm_120 FP16 matmul verification passed.")

        # sm_120 torch.compile smoke test
        model = torch.nn.Linear(16, 16).cuda().half()
        compiled = torch.compile(model, backend="inductor")
        t = torch.randn(4, 16, device="cuda", dtype=torch.float16)
        out = compiled(t)
        assert out.shape == (4, 16), "torch.compile returned incorrect shape"
        del model, compiled, t, out
        torch.cuda.empty_cache()
        print("✔ CUDA sm_120 torch.compile (inductor) smoke test passed.")
    else:
        print("⚠ CUDA is not available, skipping hardware compute checks.")

    print(f"\n🎉 Deep smoke test finished successfully across {len(nodes.NODE_CLASS_MAPPINGS)} registered nodes.")


if __name__ == "__main__":
    run_deep_smoke()

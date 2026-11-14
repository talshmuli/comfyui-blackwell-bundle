# Upstream Custom Node Compatibility Patches

This directory contains standalone compatibility patches for community custom nodes when deployed in headless container environments and modern PyTorch / CUDA 12.8 Blackwell (sm_120) runtimes:

| Patch | Target Repository | Purpose |
|---|---|---|
| `3d_pack.patch` | [ComfyUI-3D-Pack](https://github.com/MrForExample/ComfyUI-3D-Pack) | Shields optional CUDA-compilation dependencies (`nvdiffrast`, `torchtyping`, `pytorch_msssim`, `jaxtyping`) behind fallback imports so all 97 core 3D mesh nodes register cleanly without display/driver overhead. |
| `ltxvideo.patch` | [ComfyUI-LTXVideo](https://github.com/Lightricks/ComfyUI-LTXVideo) | Graceful fallback for `Gemma3` transformer classes when running standard transformers builds. |
| `rvc.patch` | [ComfyUI-RVC](https://github.com/AIFSH/ComfyUI-RVC) | Safe CLI argument parsing (`parse_known_args`) preventing collisions with ComfyUI CLI flags, eliminates global `users.pth` core module shadowing, protects reboot routes, and provides fallback definitions for training parameters during object info introspection. |
| `wanvideo.patch` | [ComfyUI-WanVideoWrapper](https://github.com/kijai/ComfyUI-WanVideoWrapper) | Safe proxy for `PromptServer.instance`, sm_120 SDPA fallback for SageAttention, and resilient temporal/spatial alignment for WanVideo ControlNet. |
| `vhs.patch` | [ComfyUI-VideoHelperSuite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite) | Flexible `VALIDATE_INPUTS` supporting optional video inputs and variable keyword arguments during UI upload validation. |
| `yue2.patch` | [ComfyUI-FL-YuE2](https://github.com/filliptm/ComfyUI-FL-YuE2) | Graceful exception handling for optional training endpoints, preserving core audio generation inference nodes. |
| `step1x.patch` | [ComfyUI-Step1X-Edit](https://github.com/Yuan-ManX/ComfyUI-Step1X-Edit) | Fixes Python 3.12 relative import syntax error (`from .src import sampling`) and adds `Step1X_` namespace prefixes to prevent node mapping collisions with core ComfyUI. |
| `comfy_path_resilience.patch` | [ComfyUI](https://github.com/comfyanonymous/ComfyUI) | Provides cross-platform Windows-to-Linux path resilience (`\` to `/` normalization) and single-match basename fallback in `folder_paths.py` and `execution.py` to prevent "Value not in list" failures on community workflows. |

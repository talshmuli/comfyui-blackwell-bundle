# Upstream Custom Node Compatibility Patches

This directory contains standalone compatibility patches for community custom nodes when deployed in headless container environments and modern PyTorch / CUDA 12.8 Blackwell (sm_120) runtimes:

| Patch | Target Repository | Purpose |
|---|---|---|
| `3d_pack.patch` | [ComfyUI-3D-Pack](https://github.com/MrForExample/ComfyUI-3D-Pack) | Shields optional CUDA-compilation dependencies (`nvdiffrast`, `torchtyping`, `pytorch_msssim`, `jaxtyping`) behind fallback imports so all 97 core 3D mesh nodes register cleanly without display/driver overhead. |
| `ltxvideo.patch` | [ComfyUI-LTXVideo](https://github.com/Lightricks/ComfyUI-LTXVideo) | Graceful fallback for `Gemma3` transformer classes when running standard transformers builds. |
| `rvc.patch` | [ComfyUI-RVC](https://github.com/AIFSH/ComfyUI-RVC) | Safe CLI argument parsing (`parse_known_args`) preventing collisions with ComfyUI CLI flags. |
| `wanvideo.patch` | [ComfyUI-WanVideoWrapper](https://github.com/kijai/ComfyUI-WanVideoWrapper) | Safe proxy for `PromptServer.instance` during headless worker and testing initialization. |

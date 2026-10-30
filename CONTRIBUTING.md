# Contributing to ComfyUI Blackwell Docker

Thank you for your interest in improving the ComfyUI Blackwell Docker build!

## How This Project Works
This repository provides automated build pipelines and Docker configurations tailored specifically for **NVIDIA Blackwell GeForce RTX 5090 and 5080 (`sm_120`)** GPUs running CUDA 12.8+.

* **Automated Builds:** GitHub Actions builds images bi-weekly (1st and 15th) via `.github/workflows/build.yml`.
* **Smart Change Detection:** Automated workflows check for upstream `ai-dock/comfyui` base updates and PyTorch nightly `cu128` releases before triggering builds.
* **Testing First:** Every build executes a CPU-safe validation suite ensuring PyTorch CUDA 12.8 runtime, `sm_120` compilation flags, Torchvision ops, and ComfyUI imports before pushing to GHCR.

## Submitting Pull Requests
1. Fork the repository and create your branch from `master`.
2. Keep changes focused and documented.
3. Test the Dockerfile locally:
   ```bash
   docker build -t test-comfyui:build -f Dockerfile .
   ```
4. Run the CI validation command locally:
   ```bash
   docker run --rm test-comfyui:build /opt/environments/python/comfyui/bin/python -c "
   import sys, importlib.util, torch, torchvision, torchvision.ops, asyncio
   assert '12.8' in torch.version.cuda
   assert 'sm_120' in torch.__config__.show()
   assert importlib.util.find_spec('xformers') is None
   _ = torchvision.ops.nms
   import numpy, numba, colour, insightface, onnx, mediapipe
   assert numpy.__version__.startswith('1.')
   sys.argv.append('--cpu')
   sys.path.append('/opt/ComfyUI')
   import comfy.options; comfy.options.enable_args_parsing()
   import server; loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop); s = server.PromptServer(loop)
   import execution, nodes; nodes.init_extra_nodes()
   assert 'VHS_VideoCombine' in nodes.NODE_CLASS_MAPPINGS
   assert 'DownloadAndLoadLivePortraitModels' in nodes.NODE_CLASS_MAPPINGS
   assert 'LatentSyncNode' in nodes.NODE_CLASS_MAPPINGS
   print('ALL LOCAL CI VALIDATION CHECKS PASSED!')
   "
   ```
5. Submit your PR with a clear description of the motivation and testing performed.

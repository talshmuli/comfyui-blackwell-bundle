# ComfyUI Docker for NVIDIA Blackwell (RTX 5090 / 5080 - sm_120)

[![Build & Publish ComfyUI Blackwell Image](https://github.com/talshmuli/comfyui-blackwell-docker/actions/workflows/build.yml/badge.svg)](https://github.com/talshmuli/comfyui-blackwell-docker/actions/workflows/build.yml)

A production-ready, containerized distribution of **ComfyUI** built specifically for **NVIDIA GeForce RTX 5090 and RTX 5080** GPUs utilizing the **Blackwell architecture (`sm_120`)** and **CUDA 12.8+**.

---

## 1. Motivation

NVIDIA GeForce RTX 50-series GPUs (RTX 5090 / 5080) are powered by the **Blackwell** architecture, which requires CUDA compute capability **`sm_120`**.

Standard ComfyUI Docker containers ship with stable PyTorch builds (PyTorch 2.4 / CUDA 12.1), which only include precompiled kernels up to `sm_90` (Hopper/Ada Lovelace). Attempting to run diffusion models or tensor operations on an RTX 5090 with standard images triggers the fatal CUDA error:
```text
RuntimeError: CUDA error: no kernel image is available for execution on the device
```

This repository bridges that gap by providing an automated, continuously updated build pipeline that layers official **PyTorch nightly builds with native CUDA 12.8 / `sm_120` kernels** directly onto the formal **`ai-dock/comfyui`** base image.

---

## 2. Architecture & How It's Built

* **Upstream Base Image:** Strictly sourced from GitHub Container Registry: [`ghcr.io/ai-dock/comfyui:latest-cuda`](https://github.com/ai-dock/comfyui).
* **PyTorch Runtime:** Official PyTorch nightly wheels (`torch>=2.12.0.dev+cu128`, `torchvision>=0.27.0.dev+cu128`) compiled with native `sm_120` compute capability.
* **Driver Libraries:** Synchronized with host NVIDIA 570+ drivers via CUDA 12.8 runtime libraries (`cudnn>=9.20`, `cublas>=12.8`, `cusolver>=11.7`, `nccl>=2.29`, `libcufile`, `libcusparseLt`, `nvshmem`).
* **Optimized Attention:** Removes incompatible `xformers` builds. PyTorch 2.x SDPA (Scaled Dot Product Attention) is natively built-in and significantly faster on Blackwell hardware.
* **Pre-Baked Video & Animation Stack:** Out-of-the-box support for video mastering, facial animation, and speech-driven lip-sync via pre-installed custom nodes: [ComfyUI-VideoHelperSuite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite) (pinned to stable release `593fcb07`), [ComfyUI-LivePortraitKJ](https://github.com/kijai/ComfyUI-LivePortraitKJ), and [ComfyUI-LatentSyncWrapper](https://github.com/ShmuelRonen/ComfyUI-LatentSyncWrapper).
* **Dependency Conflict Hardening:** Version pins (`numpy<2.0.0,>=1.24.0`, `protobuf<5,>=4.25.3`, `onnx<1.16`, `insightface`) preserve NumPy 1.x ABI stability for `colour-science`, `numba`, and face analysis. Video libraries are installed with `--no-deps` to strictly protect the Blackwell nightly PyTorch wheel from PyPI package overwrites.

---

## 3. Strict Semantic Versioning & Immutability

To guarantee reproducibility and prevent container regressions, every image published to GitHub Packages is tagged with two layers:

1. **Immutable Exact SemVer Tag:**
   ```text
   ghcr.io/talshmuli/comfyui-blackwell-docker:v0.2.2-torch2.12.0.dev-cu128-YYYYMMDD
   ```
   * Tracks the exact ComfyUI release (`v0.2.2`), PyTorch version (`2.12.0.dev`), CUDA architecture (`cu128`), and date stamp.
   * **Zero Overwrites:** Previous builds are never overwritten or deleted, ensuring reliable rollback.
2. **Canonical Series Tag:**
   ```text
   ghcr.io/talshmuli/comfyui-blackwell-docker:v0.2.2-cuda128-sm120
   ```
3. **Latest Tag:**
   ```text
   ghcr.io/talshmuli/comfyui-blackwell-docker:latest
   ```

---

## 4. Automated Bi-Weekly Schedule, Smart Change Detection & CI Validation

A GitHub Actions workflow ([`.github/workflows/build.yml`](.github/workflows/build.yml)) runs automatically **on the 1st and 15th of every month at 00:00 UTC** (bi-weekly):

* **Smart Change Detection:** Before running an expensive build, the pipeline queries:
  1. The manifest digest of upstream [`ghcr.io/ai-dock/comfyui:latest-cuda`](https://github.com/ai-dock/comfyui).
  2. The latest release of PyTorch and Torchvision nightly wheels on the CUDA 12.8 index (`https://download.pytorch.org/whl/nightly/cu128`).
  * If no upstream or package changes have occurred and repository code is unchanged, the workflow skips the build in seconds to avoid consuming runner resources.
  * If any upstream dependency or package has updated, the workflow proceeds to build the latest image.
* **Automated End-of-Pipeline CI Validation:**
  Before publishing to GitHub Container Registry, the built container runs an automated test suite verifying:
  - PyTorch CUDA 12.8 runtime detection (`assert '12.8' in torch.version.cuda`).
  - Blackwell `sm_120` compute capability presence in kernel flags (`assert 'sm_120' in torch.__config__.show()`).
  - Torchvision C++ operator loading without missing symbols (`torchvision.ops.nms`).
  - Safe uninstallation of incompatible legacy `xformers`.
  - Package dependency compatibility (`numpy<2`, `numba`, `colour-science`, `insightface`, `onnx`, `mediapipe`).
  - ComfyUI core and pre-baked custom nodes registration (`VHS_VideoCombine`, `DownloadAndLoadLivePortraitModels`, `LatentSyncNode`).
  * If any validation check fails, the pipeline aborts immediately and refuses to publish.
* **Manual Trigger:** Can also be triggered manually on demand via GitHub Actions **Workflow Dispatch** with optional `force_build` and `tag_override` options.

---

## 5. Quickstart Guide

### Prerequisites
* NVIDIA Driver $\ge$ 570.xx installed on the host.
* NVIDIA Container Toolkit installed (`nvidia-smi` accessible inside containers).

### Option A: Run with Docker Compose (Recommended)

Create a `docker-compose.yml`:
```yaml
services:
  comfyui:
    image: ghcr.io/talshmuli/comfyui-blackwell-docker:v0.2.2-cuda128-sm120
    container_name: comfyui
    restart: unless-stopped
    ports:
      - "8188:8188"
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - NVIDIA_DRIVER_CAPABILITIES=all
      - COMFYUI_FLAGS=--preview-method auto --normalvram
      - WEB_ENABLE_AUTH=false
      - CF_QUICK_TUNNELS=false
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    volumes:
      - ./models:/opt/ComfyUI/models
      - ./output:/opt/ComfyUI/output
```

Start the container:
```bash
docker compose up -d
```

Open your browser at: **`http://localhost:8188`**.

### Option B: Run with Docker CLI
```bash
docker run -d \
  --name comfyui \
  --gpus all \
  -p 8188:8188 \
  -v ./models:/opt/ComfyUI/models \
  -v ./output:/opt/ComfyUI/output \
  ghcr.io/talshmuli/comfyui-blackwell-docker:v0.2.2-cuda128-sm120
```

---

## 6. Verifying Blackwell GPU Acceleration & Custom Nodes

To verify that your RTX 5090 is recognized and executing `sm_120` GPU kernels inside the container:

```bash
docker exec comfyui /opt/environments/python/comfyui/bin/python -c \
  "import torch; print('Device:', torch.cuda.get_device_name(0)); print('Supported Archs:', torch.cuda.get_arch_list()); x = torch.randn(10, 10, device='cuda'); print('Tensor multiply OK:', (x @ x).shape)"
```

**Expected output:**
```text
Device: NVIDIA GeForce RTX 5090
Supported Archs: ['sm_75', 'sm_80', 'sm_86', 'sm_90', 'sm_100', 'sm_120']
Tensor multiply OK: torch.Size([10, 10])
```

To verify that ComfyUI and the pre-installed custom nodes are fully registered and accessible:

```bash
docker exec comfyui /opt/environments/python/comfyui/bin/python -c \
  "import execution, nodes; nodes.init_extra_nodes(); print('Total registered nodes:', len(nodes.NODE_CLASS_MAPPINGS))"
```

---

## 7. Acknowledgements & Upstream Projects

This project builds upon exceptional open-source software:
* **[ComfyUI](https://github.com/comfyanonymous/ComfyUI)** by comfyanonymous — Powerful node-based diffusion architecture.
* **[ai-dock/comfyui](https://github.com/ai-dock/comfyui)** by Rob Ballantyne — Robust multi-environment container runtime and process supervision.
* **[PyTorch](https://github.com/pytorch/pytorch)** — Official nightly CUDA 12.8 builds with native Blackwell `sm_120` compute kernels.
* **[ComfyUI-VideoHelperSuite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite)** by Kosinkadink — Video ingestion, playback, and export nodes.
* **[ComfyUI-LivePortraitKJ](https://github.com/kijai/ComfyUI-LivePortraitKJ)** by Kijai — Real-time portrait animation and facial dynamics.
* **[ComfyUI-LatentSyncWrapper](https://github.com/ShmuelRonen/ComfyUI-LatentSyncWrapper)** by Shmuel Ronen — Audio-conditioned latent lip-syncing.

---

## 8. License

This project is licensed under the [MIT License](LICENSE). ComfyUI, PyTorch, and upstream base image components are licensed under their respective open-source licenses.

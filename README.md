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
* **Driver Libraries:** Synchronized with host NVIDIA 570+ drivers via CUDA 12.8 runtime libraries (`cudnn>=9.20`, `cublas>=12.8`, `nccl>=2.29`, `libcufile`, `libcusparseLt`, `nvshmem`).
* **Optimized Attention:** Removes incompatible `xformers` builds. PyTorch 2.x SDPA (Scaled Dot Product Attention) is natively built-in and significantly faster on Blackwell hardware.

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

## 4. Automated Monthly Release Schedule

A GitHub Actions workflow ([`.github/workflows/build.yml`](.github/workflows/build.yml)) runs automatically **on the 1st of every month at 00:00 UTC**:
* Pulls the newest upstream `ai-dock` base image.
* Resolves the latest nightly PyTorch CUDA 12.8 wheels.
* Executes full build, tests GPU kernel availability, and pushes newly tagged images to GitHub Container Registry.
* Can also be triggered manually on demand via GitHub Actions **Workflow Dispatch**.

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

## 6. Verifying Blackwell GPU Acceleration

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

---

## 7. License

This repository contains build configurations and scripts under the MIT License. ComfyUI and its dependencies are subject to their respective upstream licenses.

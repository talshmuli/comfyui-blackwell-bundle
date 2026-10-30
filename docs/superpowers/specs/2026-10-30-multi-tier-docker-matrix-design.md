# Design Spec: Multi-Tier Docker Image Matrix & Modular VFX Orchestration

**Status:** Proposed  
**Author:** AI Coding Assistant & Tal Shmuli  
**Date:** 2026-10-30  
**Target Workstation:** NVIDIA GeForce RTX 5090 Blackwell (32GB GDDR7, sm_120) / AMD Ryzen 9 9950X3D  
**Repository:** `talshmuli/comfyui-blackwell-docker` (`feat/matrix-builds-blender-worker`)

---

## 1. Executive Summary & Motivation

### The Problem
Modern generative VFX and 3D character animation require a synchronized software stack combining:
1. Deep learning frameworks compiled with bleeding-edge Blackwell `sm_120` CUDA 12.8 kernels.
2. ComfyUI with a delicate web of custom nodes (LivePortrait, LatentSync, VideoHelperSuite, AnimateDiff).
3. 3D kinematic modeling engines (Blender 4.4 LTS headless) for procedural rigging and geometric AOV passes.

Packaging everything into a single monolithic 19 GB container forces users with lightweight workflows (e.g., text-to-image or custom node development) to pull gigabytes of unwanted 3D rendering tooling. Conversely, running disparate manual environments causes dependency and ABI hell.

### The Solution: Multi-Tier Matrix + Modular Studio Microservices
We introduce a 4-tier Docker build matrix and a modular Docker Compose orchestration system:
* **Tier 1 (`base`):** Minimalist ComfyUI core on PyTorch Nightly CUDA 12.8 sm_120 (~12 GB).
* **Tier 2 (`nodes`):** Generative video & character animation workstation (~16 GB) with all verified video/portrait custom nodes.
* **Tier 3 (`blender-worker`):** Lean headless Blender 4.4 LTS pass renderer (~3.5 GB) with OptiX/CUDA sm_120 acceleration and automated API runners.
* **Tier 4 (`full`):** All-in-one studio monolith (~19 GB) uniting `nodes` + `blender` for users wanting zero-compose simplicity.

In production, `nodes` + `blender-worker` form a high-throughput microservices pipeline connected via a shared render bus (`passes_bus`) and internal Docker network (`vfx-net`), isolating memory leaks and compute crashes while enabling pipelined rendering.

---

## 2. Docker Architecture & Multi-Stage Target Hierarchy

```mermaid
flowchart TD
    Upstream["ghcr.io/ai-dock/comfyui:latest-cuda"] --> Base["Target: base<br/>- PyTorch Nightly cu128 (sm_120)<br/>- CUDA 12.8 runtime & drivers<br/>- Clean ComfyUI v0.2.2<br/>- No custom nodes"]
    Base --> Nodes["Target: nodes<br/>- VideoHelperSuite<br/>- LivePortraitKJ<br/>- LatentSyncWrapper<br/>- AnimateDiff-Evolved<br/>- ComfyUI-3D-Pack<br/>- Pinned diffusers & torchmetrics"]
    Nodes --> Full["Target: full (Monolith)<br/>- nodes layer<br/>- Blender 4.4 LTS Linux x64<br/>- ComfyUI-BlenderAI addon"]
    
    UbuntuBase["ubuntu:24.04 (or base)"] --> BlenderWorker["Target: blender-worker<br/>- Blender 4.4.3 LTS Headless<br/>- CUDA 12.8 & OptiX sm_120<br/>- Python 3.11 bpy & runner scripts<br/>- ComfyUI-BlenderAI-node addon"]
```

### Stage Details

1. **`base` (Target: `base`)**:
   - Base: `ghcr.io/ai-dock/comfyui:latest-cuda`
   - Actions: Installs PyTorch nightly cu128, uninstalls xformers (ABI safety), installs CUDA 12.8 drivers.
   - Nodes: 0 custom nodes.

2. **`nodes` (Target: `nodes`)**:
   - Base: `base`
   - Custom Nodes: `ComfyUI-VideoHelperSuite`, `ComfyUI-LivePortraitKJ`, `ComfyUI-LatentSyncWrapper`, `ComfyUI-AnimateDiff-Evolved`, `ComfyUI-3D-Pack`.
   - Python Libraries: Pinned `diffusers>=0.30.0,<0.31.0`, `huggingface-hub<1.0`, `insightface`, `mediapipe<0.10.15`, `onnx<1.16`, `plyfile`, `trimesh`, `pyhocon`.

3. **`blender-worker` (Target: `blender-worker`)**:
   - Dedicated headless worker.
   - Installs Blender 4.4.3 Linux x64 tarball, adds symlink `/usr/local/bin/blender`.
   - Copies automated render scripts and installs `ComfyUI-BlenderAI-node` to `/opt/blender/4.4/scripts/addons/`.
   - Entrypoint: listens for rendering tasks or runs headless CLI batch commands against `/workspace/passes`.

4. **`full` (Target: `full`)**:
   - Inherits directly from `nodes`.
   - Installs Blender 4.4.3 and symlinks.
   - Provides the complete one-stop shop.

---

## 3. GitHub Actions CI Matrix (`build.yml`)

The CI workflow will execute a parallel matrix build strategy:

```yaml
jobs:
  build-and-publish:
    runs-on: ubuntu-24.04
    strategy:
      fail-fast: false
      matrix:
        flavor:
          - target: base
            tag_suffix: base
            test_type: core
          - target: nodes
            tag_suffix: nodes
            test_type: custom_nodes
          - target: blender-worker
            tag_suffix: blender-worker
            test_type: blender
          - target: full
            tag_suffix: full
            test_type: full
```

### CI Step Pipeline for Each Matrix Worker:
1. Checkout code (`actions/checkout@v7`).
2. Secret scan with TruffleHog.
3. Build container with `docker/buildx` targeting `--target ${{ matrix.flavor.target }}`.
4. Run automated sm_120 and flavor-specific integrity tests.
5. Audit filesystem for exposed credentials.
6. Aqua Security Trivy vulnerability scan (`format: table` and `format: sarif`).
7. Upload SARIF to GitHub Security Tab via `github/codeql-action/upload-sarif@v4` (zero deprecations).
8. Upload SARIF artifact via `actions/upload-artifact@v4` (downloadable on Actions run page).
9. Tag and publish to `ghcr.io/talshmuli/comfyui-blackwell-docker:<version>-<flavor>`.

---

## 4. Docker Compose Orchestration (`docker-compose.yml`)

`docker-compose.yml` provides three operational profiles:

### 1. Modular Studio Profile (`--profile modular`, Default Recommended)
```yaml
services:
  comfyui:
    image: ghcr.io/talshmuli/comfyui-blackwell-docker:nodes-cuda128-sm120
    container_name: comfyui-nodes
    profiles: ["modular"]
    ports:
      - "8188:8188"
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - COMFYUI_FLAGS=--preview-method auto --normalvram
      - WEB_ENABLE_AUTH=false
    volumes:
      - ./data/models:/opt/ComfyUI/models
      - ./data/output:/opt/ComfyUI/output
      - passes_bus:/opt/ComfyUI/input/passes
    networks:
      - vfx-net
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

  blender-worker:
    image: ghcr.io/talshmuli/comfyui-blackwell-docker:blender-worker
    container_name: blender-worker
    profiles: ["modular"]
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - COMFYUI_API_URL=http://comfyui:8188
    volumes:
      - ./data/blender_scenes:/workspace/scenes
      - passes_bus:/workspace/passes
    networks:
      - vfx-net
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

volumes:
  passes_bus:

networks:
  vfx-net:
    driver: bridge
```

### 2. Full Monolith Profile (`--profile full`)
Runs `comfyui-full` (all-in-one).

### 3. Base Core Profile (`--profile base`)
Runs `comfyui-base` on port 8188.

---

## 5. Safety & Zero Impact to Running Production Environment
* The host currently has a running container `comfyui` on port `8188`.
* All local build testing will build isolated tags (`local-test-base:test`, `local-test-nodes:test`, `local-test-blender:test`).
* Compose integration tests will run on test port `8189` and test network `vfx-test-net` with `docker compose -p test-modular up`, ensuring zero interruption or port collision with the live system.

---

## 6. Documentation Enhancements

`README.md` will be updated with:
1. **The 4-Tier Matrix Table:** Specs, sizes, and recommended use cases.
2. **Expanded Motivation: The One-Stop Shop Rationale:**
   - Why containerized CUDA 12.8 + sm_120 is essential for Blackwell RTX 5090 / 5080.
   - Why microservices (`nodes` + `blender-worker`) provide crash-resilient 3D-to-neural rendering.
   - Comprehensive workflow examples for both modular and monolithic deployments.

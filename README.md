# ComfyUI & Blender VFX Studio Bundle for NVIDIA Blackwell (RTX 5090 / 5080 - sm_120)

[![Build & Publish ComfyUI Blackwell Bundle](https://github.com/talshmuli/comfyui-blackwell-bundle/actions/workflows/build.yml/badge.svg)](https://github.com/talshmuli/comfyui-blackwell-bundle/actions/workflows/build.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![CUDA: 12.8](https://img.shields.io/badge/CUDA-12.8-green.svg)](https://developer.nvidia.com/cuda-toolkit)
[![Compute: sm_120](https://img.shields.io/badge/Architecture-Blackwell%20sm__120-orange.svg)](https://www.nvidia.com/en-us/geforce/rtx-5090/)
[![Docker Image: GHCR](https://img.shields.io/badge/GHCR-Docker%20Registry-blue)](https://github.com/talshmuli/comfyui-blackwell-bundle/pkgs/container/comfyui-blackwell-bundle)

A production-grade, containerized generative AI studio engineered specifically for **NVIDIA GeForce RTX 5090 and RTX 5080** GPUs utilizing the **Blackwell microarchitecture (`sm_120`)**, **CUDA 12.8+**, **PyTorch Nightly**, and **Blender 4.4 LTS**.

Includes a comprehensive pre-installed suite of state-of-the-art custom nodes for **Video Generation**, **3D Asset Creation**, **Multilingual Audio & Singing**, and **Vision Guidance**, backed by **Smart ComfyUI Gallery** for digital asset cataloging and workflow restoration.

---

## Table of Contents

- [1. Executive Summary & Blackwell Optimization](#1-executive-summary--blackwell-optimization)
  - [The Blackwell sm_120 Challenge](#the-blackwell-sm_120-challenge)
  - [The Solution: Multi-Stage Container Suite](#the-solution-multi-stage-container-suite)
- [2. Who This Bundle Is For (and What It Is NOT)](#2-who-this-bundle-is-for-and-what-it-is-not)
- [3. Pre-Installed Custom Node Suite](#3-pre-installed-custom-node-suite)
  - [Video Generation & Temporal Diffusion](#video-generation--temporal-diffusion)
  - [3D Generation & Spatial Kinematics](#3d-generation--spatial-kinematics)
  - [Audio, Voice & Music Production](#audio-voice--music-production)
  - [Vision Guidance & Workflow Utilities](#vision-guidance--workflow-utilities)
- [4. Companion Service: Smart ComfyUI Gallery](#4-companion-service-smart-comfyui-gallery)
- [5. 4-Tier Multi-Stage Image Matrix](#5-4-tier-multi-stage-image-matrix)
- [6. Quick Start Guide](#6-quick-start-guide)
  - [Prerequisites](#prerequisites)
  - [Directory Layout & Volume Mounts](#directory-layout--volume-mounts)
  - [Launching Deployment Profiles](#launching-deployment-profiles)
  - [Environment Configuration (.env)](#environment-configuration-env)
- [7. Verification & Health Checks](#7-verification--health-checks)
- [8. Performance Tuning Notes for RTX 5090 / 5080](#8-performance-tuning-notes-for-rtx-5090--5080)
  - [VRAM Management & Memory Flags](#vram-management--memory-flags)
  - [Attention Kernels & SDPA on sm_120](#attention-kernels--sdpa-on-sm_120)
  - [torch.compile on Blackwell](#torchcompile-on-blackwell)
  - [Tiled VAE Decoding for Long Video](#tiled-vae-decoding-for-long-video)
  - [Quantization Matrix: Native FP8 & GGUF](#quantization-matrix-native-fp8--gguf)
- [9. Curated Production Workflows](#9-curated-production-workflows)
- [10. Security, Supply Chain & Immutability](#10-security-supply-chain--immutability)
- [11. Acknowledgements & Upstream Projects](#11-acknowledgements--upstream-projects)
- [12. License](#12-license)

---

## 1. Executive Summary & Blackwell Optimization

### The Blackwell sm_120 Challenge

NVIDIA GeForce RTX 50-series GPUs (RTX 5090, RTX 5080) are built on NVIDIA's **Blackwell** microarchitecture, requiring CUDA compute capability **`sm_120`**.

Standard ComfyUI Docker images ship with stable PyTorch builds (PyTorch 2.4/2.5 on CUDA 12.1/12.4), which only provide precompiled CUDA kernels up to `sm_90` (Hopper/Ada Lovelace). Launching diffusion or DiT models on an RTX 50-series GPU with standard images causes the fatal error:

```text
RuntimeError: CUDA error: no kernel image is available for execution on the device
```

Furthermore, advanced generative pipelines—such as video diffusion, 3D asset generation, facial performance capture, and audio-driven lip-sync—demand a tightly synchronized software ecosystem:
1. Deep learning frameworks compiled natively with **CUDA 12.8+** and Blackwell **`sm_120`** compute kernels.
2. Verified custom nodes tested together with zero Python package conflicts.
3. A headless 3D engine (**Blender 4.4 LTS**) to generate geometric AOV passes (Depth, Normal, OpenPose) and feed them directly into neural pipelines.
4. A companion digital asset management tool to track, compare, and restore workflows across hundreds of iterations.

### The Solution: Multi-Stage Container Suite

This repository provides an automated, production-tested container suite that completely resolves the Blackwell kernel gap:
* **Native sm_120 PyTorch Nightly:** Built from official nightly wheels compiled with CUDA 12.8 and sm_120 kernels, running with `cudnn>=9.20` and `cublas>=12.8`.
* **Zero Legacy ABI Conflicts:** Incompatible legacy `xformers` wheels (which lack sm_120 support and cause runtime crashes) are cleanly purged in favor of native PyTorch 2.x Scaled Dot-Product Attention (SDPA).
* **PyTorch Version Guardrail (`PIP_CONSTRAINT`):** Establishes an environment-level constraint file locking the exact nightly CUDA 12.8 `sm_120` PyTorch binaries, preventing community custom node installers from downgrading your PyTorch build.
* **Modular Microservices vs. All-in-One Monolith:** Deploy as independent microservices (`comfyui-nodes` + `blender-worker` + `smartgallery`) sharing an inter-container render bus, or as an all-in-one monolith (`comfyui-full`).

```
       ┌────────────────────────────────────────────────────────┐
       │                   Docker Compose VFX                   │
       │                                                        │
       │   ┌───────────────────┐        ┌───────────────────┐   │
       │   │   comfyui-nodes   │        │  blender-worker   │   │
       │   │   (CUDA 12.8 /    │        │  (Blender 4.4.3   │   │
       │   │    sm_120 / Nodes)│        │   OptiX / CUDA)   │   │
       │   └─────────▲─────────┘        └─────────┬─────────┘   │
       │             │                            │             │
       │             │   passes_bus (Shared Vol)  │             │
       │             └─── /opt/ComfyUI/input/ ────┘             │
       │                  passes <──> /workspace/passes         │
       │                                                        │
       │   ┌───────────────────┐                                │
       │   │    smartgallery   │                                │
       │   │ (Catalog & Search │                                │
       │   │    Port 8189)     │                                │
       │   └───────────────────┘                                │
       │                                                        │
       │   ═════════════════ vfx-net (Bridge) ═══════════════   │
       └────────────────────────────────────────────────────────┘
```

---

## 2. Who This Bundle Is For (and What It Is NOT)

### 🎯 Who Will Enjoy This Bundle
* **NVIDIA Blackwell GPU Owners (RTX 5090 / 5080 / 5070):** Creators and engineers seeking native hardware `sm_120` execution with zero CUDA kernel mismatches or manual compilation headaches.
* **Generative Video & Digital Human Creators:** Studios generating high-resolution video using Wan 2.1, LTX-Video, AnimateDiff, LivePortrait, and LatentSync.
* **3D Generative Artists & Technical Directors:** Artists producing meshes, point clouds, and Gaussian splats via ComfyUI-3D-Pack, paired with Blender 4.4 LTS headless AOV pass rendering.
* **Quantized Model Practitioners:** Workstations running heavy 12B+ diffusion models (FLUX.1 Dev/Schnell, SD 3.5, Wan 2.1, HunyuanVideo) at 4-bit, 5-bit, or 8-bit precision using native `ComfyUI-GGUF` and official FP8.
* **Production Studios & Homelabs:** Users requiring verified container security (0 Critical CVEs, Pillow 13 source compilation, automated Aqua Trivy audits, and locked PyTorch kernels).

### 🚫 What This Bundle Is NOT For
* **Non-NVIDIA or Legacy Hardware:** Not intended for AMD GPUs (ROCm), Apple Silicon (MPS), Intel GPUs (ARC), or older pre-Turing NVIDIA architectures (GTX 10-series or earlier).
* **Experimental / Fragile Third-Party C++ Formats:** Not for experimental proprietary engines (such as MIT Nunchaku SVDQuant) that require hardcoded C++ wheels tied to specific PyTorch builds or force lowering container security (`security_level = weak`). We prioritize industry-standard, rock-solid **Native FP8 and GGUF**.
* **Global Experimental Attention Kernel Overrides:** We avoid forcing global experimental attention kernels (like `--use-sage-attention`) that are known to produce black frames on video models like Wan 2.1 and SD 1.5.
* **Barebones "Clean Slate" Minimalists:** If you only need an empty 50MB Python container and prefer manually downloading every node and debugging dependency conflicts from scratch, the pre-configured video/3D workstation may be heavier than what you need (though our `base` profile provides a clean starting point).

---

## 3. Pre-Installed Custom Node Suite

The `nodes` and `full` images ship with over 2,000 pre-verified, registered node types across the entire generative AI spectrum.

### Video Generation & Temporal Diffusion

| Custom Node Repository | Key Features & Capabilities |
| :--- | :--- |
| **[ComfyUI-WanVideoWrapper](https://github.com/kijai/ComfyUI-WanVideoWrapper)** *(by kijai)* | High-performance implementation of Wan 2.1 (1.3B & 14B) Text-to-Video and Image-to-Video. Native Blackwell sm_120 support, auto text-encoder offloading, dynamic memory scaling, and tiled VAE decode. |
| **[ComfyUI-LTXVideo](https://github.com/Lightricks/ComfyUI-LTXVideo)** *(by Lightricks)* | Ultra-fast DiT video synthesis (LTX-2, 2.3, 2.5). Features single-stage and two-stage distillation, IC-LoRA camera/motion control, inpaint/outpaint, and HDR pipelines. |
| **[ComfyUI-AnimateDiff-Evolved](https://github.com/Kosinkadink/ComfyUI-AnimateDiff-Evolved)** *(by Kosinkadink)* | Temporal motion modules, sliding context window, motion LoRAs, and prompt travel for continuous character and camera animation. |
| **[ComfyUI-LivePortraitKJ](https://github.com/kijai/ComfyUI-LivePortraitKJ)** *(by kijai)* | High-speed expressive facial reenactment, driving video, head pose, eye blink, and lip motion retargeting. |
| **[ComfyUI-LatentSyncWrapper](https://github.com/ShmuelRonen/ComfyUI-LatentSyncWrapper)** *(by Shmuel Ronen)* | Audio-conditioned facial lip-synchronization pipeline for realistic digital human performance. |
| **[ComfyUI-Frame-Interpolation](https://github.com/Fannovel16/ComfyUI-Frame-Interpolation)** *(by Fannovel16)* | Temporal smoothing and frame rate upscaling using RIFE, FILM, and AMT algorithms for buttery smooth 60 FPS / 120 FPS output. |
| **[ComfyUI-VideoHelperSuite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite)** *(by Kosinkadink)* | Core video utility suite: video loading, batched latent combination, audio muxing, and high-quality MP4/WebM/GIF encoding (`VHS_VideoCombine`). |

### 3D Generation & Spatial Kinematics

| Custom Node Repository | Key Features & Capabilities |
| :--- | :--- |
| **[ComfyUI-3D-Pack](https://github.com/MrForExample/ComfyUI-3D-Pack)** *(by MrForExample)* | Comprehensive 3D generative suite supporting: <br>• Single-image to 3D mesh (InstantMesh, TripoSR, CRM, Stable3DGen Trellis).<br>• 3D Gaussian Splatting (3DGS) and Neural Radiance Fields (NeRF) rendering.<br>• Geometric operators: Decimate Mesh, Remesh, Normal extraction, UV unwrapping, and KiUI / TBB integration. |
| **[ComfyUI-BlenderAI-node](https://github.com/AIGODLIKE/ComfyUI-BlenderAI-node)** *(by AIGODLIKE)* | Direct integration bridge with Blender 4.4 LTS for automated scene loading, procedural camera animation, and AOV pass rendering (Depth, Normal, OpenPose, Mist). |

### Audio, Voice & Music Production

| Custom Node Repository | Key Features & Capabilities |
| :--- | :--- |
| **[ComfyUI-FL-YuE2](https://github.com/filliptm/ComfyUI-FL-YuE2)** *(by filliptm)* | Full-song generation engine producing multi-genre compositions with vocal and instrumental tracks from structured lyrics. |
| **[Comfyui-Song-Generation-Suite](https://github.com/pmarmotte2/Comfyui-Song-Generation-Suite)** *(by pmarmotte2)* | Complete musical score composition, audio adapter training, and multi-track audio generation workflows. |
| **[ComfyUI-RVC](https://github.com/AIFSH/ComfyUI-RVC)** *(by AIFSH)* | Retrieval-based Voice Conversion for vocal timbre cloning, pitch extraction (RMVPE/Harvest), and voice alteration. |

### Vision Guidance & Workflow Utilities

| Custom Node Repository | Key Features & Capabilities |
| :--- | :--- |
| **[comfyui_controlnet_aux](https://github.com/Fannovel16/comfyui_controlnet_aux)** *(by Fannovel16)* | Complete suite of ControlNet annotators: DWPose, OpenPose, Depth Anything (v1/v2), MiDaS, Canny, LineArt, and NormalBae. |
| **[ComfyUI_IPAdapter_plus](https://github.com/cubiq/ComfyUI_IPAdapter_plus)** *(by cubiq)* | Image Prompt Adapter for style reference, FaceID consistency, regional conditioning, and cross-frame character identity persistence. |
| **[ComfyUI-GGUF](https://github.com/city96/ComfyUI-GGUF)** *(by city96)* | Quantized inference engine supporting 4-bit, 5-bit, and 8-bit precision (Q4_K_M, Q5_K_M, Q8_0) for massive 12B+ models (FLUX.1, SD 3.5, Wan 2.1, HunyuanVideo). |
| **[ComfyUI-KJNodes](https://github.com/kijai/ComfyUI-KJNodes)** *(by kijai)* | Indispensable workflow utilities: color correction, image batching, condition averaging, latent masking, and VAE optimization. |
| **[ComfyUI-Copilot](https://github.com/AIDC-AI/ComfyUI-Copilot)** *(by AIDC-AI)* | In-canvas AI workflow assistant for node discovery, graph debugging, and prompt refinement. |

---

## 4. Companion Service: Smart ComfyUI Gallery

The stack includes an optional companion container: **Smart ComfyUI Gallery** (`mmartial/smart-comfyui-gallery:latest`), accessible on port **`8189`**.

```
   ┌──────────────────────────────────────────────────────────────┐
   │             Smart ComfyUI Gallery (Port 8189)                │
   │                                                              │
   │  [Visual Asset Grid]    [Search & Filter]    [A/B Compare]   │
   │  • Output Images        • Search by Prompt   • Side-by-Side  │
   │  • Video Playback       • Filter by Model    • Difference    │
   │  • Audio Previews       • Filter by Seed     • Loupe Zoom    │
   │                                                              │
   │  [Workflow Restoration]                                      │
   │  • Inspect embedded ComfyUI graph metadata                   │
   │  • One-click export / reload into active ComfyUI session    │
   └──────────────────────────────────────────────────────────────┘
```

### Key Gallery Capabilities:
* **Real-Time Visual Indexing:** Automatically monitors `./data/output` and indexes new images, animations, and video files as soon as ComfyUI writes them.
* **Metadata Extraction & Search:** Reads embedded PNG/WebP/MP4 generation metadata, enabling full-text search across prompts, negative prompts, model checkpoints, samplers, CFG scales, and seeds.
* **Side-by-Side A/B Comparison:** Compare two generations side-by-side with slider and split views to evaluate model weights, LoRA strengths, or sampler parameters.
* **Workflow Inspection & Restoration:** View the exact node graph used to create any visual asset. Directly restore the workflow back into ComfyUI with a single click.

---

## 5. 4-Tier Multi-Stage Image Matrix

| Target Stage | Canonical Tag | Estimated Size | Included Components & Features | Primary Use Case |
| :--- | :--- | :--- | :--- | :--- |
| **`base`** | `base-cuda128-sm120` | ~12 GB | • Official PyTorch Nightly CUDA 12.8 (`sm_120`)<br>• CUDA 12.8 driver runtime (`cudnn>=9.20`, `cublas>=12.8`)<br>• Clean ComfyUI core (0 custom nodes)<br>• Incompatible `xformers` uninstalled | Minimalist runtime, core testing, building custom node sets from scratch. |
| **`nodes`** *(Default)* | `nodes-cuda128-sm120`<br>`latest` | ~16 GB | • All `base` components<br>• Full Video, 3D, Audio, and Utility custom nodes<br>• Pinned ML packages (`diffusers<0.31`, `insightface`, `mediapipe`, `gguf`)<br>• Paired with `smartgallery` on port 8189 | Production generative video, character animation, facial performance capture, quantized FLUX/video diffusion. |
| **`blender-worker`** | `blender-worker`<br>`blender-4.4-worker` | ~3.5 GB | • Minimal `nvidia/cuda:12.8.0-base-ubuntu24.04`<br>• Official Blender 4.4.3 LTS Headless<br>• Native OptiX & CUDA Blackwell rendering<br>• `ComfyUI-BlenderAI-node` pre-installed<br>• Automated batch render runner (`blender_runner.py`) | Headless geometric pass generation (Depth, Normal, OpenPose), procedural 3D rigging. Pairs with `nodes` via shared volume. |
| **`full`** | `full-cuda128-sm120` | ~19 GB | • All `nodes` components (Video, Portrait, 3D, Audio, GGUF)<br>• Official Blender 4.4.3 LTS Headless<br>• `ComfyUI-BlenderAI-node` addon<br>• Native OptiX & CUDA Blackwell rendering | All-in-one single-container studio — ComfyUI + all custom nodes + Blender 4.4 in one image. Ideal for single-GPU workstations. |

---

## 6. Quick Start Guide

### Prerequisites
* **Operating System:** Linux (Ubuntu 22.04/24.04, Debian 12, Arch) or Windows via WSL2.
* **NVIDIA GPU:** GeForce RTX 5090 (32GB) or RTX 5080 (16GB) (Blackwell architecture).
* **NVIDIA Host Driver:** Version $\ge$ 570.xx installed on the host.
* **Container Runtime:** Docker Engine 24.0+ and Docker Compose v2.20+.
* **NVIDIA Container Toolkit:** Installed and configured (`nvidia-ctk runtime configure --runtime=docker`).

Verify host GPU accessibility:
```bash
docker run --rm --gpus all nvidia/cuda:12.8.0-base-ubuntu24.04 nvidia-smi
```

### Directory Layout & Volume Mounts

The repository organizes data cleanly across host volumes:

```text
comfyui-blackwell-docker/
├── docker-compose.yml          # Compose orchestration with modular/monolith profiles
├── Dockerfile                  # Multi-stage Dockerfile (base, nodes, blender-worker, full)
├── .env.example                # Sample environment configuration file
├── data/
│   ├── models/                 # Model checkpoints, LoRAs, VAE, GGUF, ControlNet
│   ├── output/                 # ComfyUI rendered images, video clips, and audio
│   ├── input/                  # Reference portraits, audio files, and driving videos
│   ├── blender_scenes/         # .blend scene files for headless Blender rendering
│   └── smartgallery/           # SQLite database and thumbnails for Smart Gallery
├── workflows/                  # Curated production workflows mounted into ComfyUI
└── scripts/                    # Validation, security audit, and runner scripts
```

#### Volume Mounts Mapping:
* **`./data/models` $\rightarrow$ `/opt/ComfyUI/models`:** Host folder for checkpoint weights, diffusion models, LoRAs, VAEs, and text encoders.
* **`./data/output` $\rightarrow$ `/opt/ComfyUI/output`:** Output folder for generated media, automatically indexed by Smart Gallery.
* **`./data/input` $\rightarrow$ `/opt/ComfyUI/input`:** Input assets (audio, keyframe portraits, reference videos).
* **`./workflows` $\rightarrow$ `/opt/ComfyUI/user/default/workflows`:** Curated workflow library directly accessible in ComfyUI's native workflow browser.
* **`passes_bus` (Docker Volume):** High-speed inter-container shared volume bridging Blender (`/workspace/passes`) to ComfyUI (`/opt/ComfyUI/input/passes`).

### Launching Deployment Profiles

Clone the repository and choose your profile:

```bash
git clone https://github.com/talshmuli/comfyui-blackwell-bundle.git
cd comfyui-blackwell-bundle
cp .env.example .env
```

#### Option A: Modular Studio Pipeline (Recommended)
Launches the synchronized microservices architecture: ComfyUI with all video/3D nodes, the dedicated Blender headless worker, and Smart Gallery:

```bash
docker compose --profile modular up -d
```
* **ComfyUI Web Interface:** [`http://localhost:8188`](http://localhost:8188)
* **Smart ComfyUI Gallery:** [`http://localhost:8189`](http://localhost:8189)
* **Shared Render Bus:** Blender passes in `/workspace/passes` appear instantly in ComfyUI at `/opt/ComfyUI/input/passes`.

#### Option B: Standalone Workstation with Gallery
Runs the full ComfyUI nodes stack alongside the Smart Gallery companion (without the Blender worker):

```bash
docker compose --profile nodes up -d
```

#### Option C: Full Studio Monolith (All-In-One)
Runs the single all-in-one container with ComfyUI, all custom nodes, and Blender 4.4 LTS bundled together:

```bash
docker compose --profile monolith up -d
```

#### Option D: Developer / Clean Core Mode
Runs the clean, minimal base ComfyUI container (0 custom nodes) alongside Blender:

```bash
docker compose --profile dev up -d
```

### Environment Configuration (.env)

Customize networking, user permissions, and GPU memory by editing `.env`:

```bash
# Network binding (bind to 127.0.0.1 for local privacy against LAN snooping)
COMFYUI_BIND_IP=0.0.0.0
COMFYUI_PORT=8188
SMARTGALLERY_BIND_IP=0.0.0.0
SMARTGALLERY_PORT=8189

# User & Group ID mapping (match host user to prevent permission issues)
PUID=1000
PGID=1000
UMASK=0022

# GPU VRAM & Memory flags
RESERVE_VRAM=1.5
COMFYUI_FLAGS=--preview-method auto --highvram
SHM_SIZE=16gb
```

---

## 7. Verification & Health Checks

Verify your deployment with these one-liner commands:

### 1. Verify PyTorch Blackwell sm_120 Execution:
```bash
docker exec comfyui-nodes /opt/environments/python/comfyui/bin/python -c \
  "import torch; print('Device:', torch.cuda.get_device_name(0)); print('Archs:', torch.cuda.get_arch_list()); x = torch.randn(10, 10, device='cuda'); print('Tensor multiply OK:', (x @ x).shape)"
```
**Expected output:**
```text
Device: NVIDIA GeForce RTX 5090
Archs: ['sm_75', 'sm_80', 'sm_86', 'sm_90', 'sm_100', 'sm_120']
Tensor multiply OK: torch.Size([10, 10])
```

### 2. Verify ComfyUI Custom Node Registration:
```bash
docker exec comfyui-nodes /opt/environments/python/comfyui/bin/python -c \
  "import execution, nodes; nodes.init_extra_nodes(); print('Total registered nodes:', len(nodes.NODE_CLASS_MAPPINGS))"
```
**Expected output:**
```text
Total registered nodes: 2020+
```

### 3. Verify Specific Pipeline Nodes:
```bash
docker exec comfyui-nodes /opt/environments/python/comfyui/bin/python -c \
  "import execution, nodes; nodes.init_extra_nodes(); \
   expected = ['VHS_VideoCombine', 'DownloadAndLoadLivePortraitModels', 'LatentSyncNode', 'WanVideoModelLoader', 'Load3D', 'UnetLoaderGGUF']; \
   missing = [n for n in expected if n not in nodes.NODE_CLASS_MAPPINGS]; \
   assert not missing, f'Missing nodes: {missing}'; \
   print('✔ All core pipeline nodes verified!')"
```

### 4. Verify Blender Headless Worker:
```bash
docker exec blender-worker blender -b --version
```
**Expected output:**
```text
Blender 4.4.3 (hash 802179c51ccc built ...)
```

### 5. Verify Smart ComfyUI Gallery Connectivity:
```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8189
```
**Expected output:**
```text
200
```

---

## 8. Performance Tuning Notes for RTX 5090 / 5080

### VRAM Management & Memory Flags

The GeForce RTX 5090 features **32GB of high-speed GDDR7 memory** on a 512-bit bus (~1,792 GB/s bandwidth), while the RTX 5080 features **16GB GDDR7** on a 256-bit bus (~960 GB/s bandwidth).

* **RTX 5090 (32GB):** Set `COMFYUI_FLAGS="--preview-method auto --highvram"`.
  32GB of VRAM allows keeping massive 14B models (Wan 2.1 14B Q4/FP8, FLUX.1 Dev FP8) resident in VRAM alongside CLIP/T5 text encoders and VAE, completely eliminating offloading latency between sampling iterations.
* **RTX 5080 (16GB):** Set `COMFYUI_FLAGS="--preview-method auto --normalvram"`.
  ComfyUI's dynamic offloading automatically swaps text encoders into host system memory before DiT sampling begins, keeping peak VRAM comfortably within 16GB.
* **VRAM Headroom Buffer (`--reserve-vram 1.5`):**
  Leaves a 1.5GB safety margin for system display servers (X11/Wayland) or external desktop applications, preventing out-of-memory driver crashes.
* **Prevent VRAM Fragmentation:**
  The container pre-configures `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`. This enables PyTorch's virtual memory allocator to dynamically expand memory segments, eliminating CUDA OOM errors caused by memory fragmentation during repeated model switching.
* **Shared Memory (`shm_size: 16gb`):**
  Docker's default 64MB shared memory causes immediate `Bus error (core dumped)` crashes when decoding high-resolution 81-frame video latents. All compose services allocate `shm_size: 16gb`.

### Attention Kernels & SDPA on sm_120

* **Native PyTorch Scaled Dot-Product Attention (SDPA):**
  PyTorch 2.x SDPA is fully optimized for Blackwell `sm_120`. On 5th-generation Tensor Cores, SDPA automatically routes through hardware-accelerated FlashAttention-like CUDA kernels natively with zero external dependencies.
* **Why Legacy xFormers is Removed:**
  Legacy `xformers` does not provide Blackwell `sm_120` binaries. Attempting to run legacy xFormers triggers missing symbol errors or forces slow CPU fallback paths.
* **Caution Regarding Global SageAttention:**
  Do not use global `--use-sage-attention`. Certain video diffusion models (specifically Wan 2.1 and SD 1.5) produce black frames or severe numerical clipping when forced into experimental attention paths. Native PyTorch SDPA delivers maximum numerical stability and near-identical throughput.

### torch.compile on Blackwell

PyTorch nightly CUDA 12.8 includes native Blackwell `sm_120` support in `torch.compile` via the Inductor and Triton backends.
* For long iterative generation batches, passing `--fast` enables operator fusion and reduced Python runtime overhead.

### Tiled VAE Decoding for Long Video

When generating high-resolution video (720p or 1080p) across 81+ frames using Wan 2.1 or LTX-Video, decoding full temporal latents simultaneously can cause sudden VRAM spikes.
* Always enable **Tiled VAE Decode** (tile size: 512, temporal tile size: 16) in your workflow. This processes spatial tiles independently, keeping peak decoding VRAM under 8GB.

### Quantization Matrix: Native FP8 & GGUF

| Pipeline | Model Checkpoint | Text Encoder & Conditioning | VRAM Footprint | Optimization Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **FLUX.1 (dev/schnell)** | `flux1-dev-fp8.safetensors` or `flux1-dev-Q8_0.gguf` | `t5xxl_fp8_e4m3fn` + `clip_l` | ~16–18 GB | **Zero offload needed.** Entire pipeline fits in VRAM on RTX 5090. Set `COMFYUI_FLAGS=--highvram`. |
| **Wan 2.1 (1.3B)** | `wan2.1_t2v_1.3B_bf16.safetensors` | Built-in CLIP / text encoder | ~8–10 GB | **Full precision (BF16).** Fits comfortably on RTX 5080 and 5090; rapid video prototyping. |
| **Wan 2.1 (14B)** | `wan2.1_t2v_14B_fp8_e4m3fn.safetensors` or `wan2.1-i2v-14B-Q4_K_M.gguf` | `umt5_xxl_fp8_e4m3fn` | ~20–24 GB | **Dynamic Offload + Tiled VAE.** Default `--normalvram` automatically swaps text encoder out before DiT sampling. Use Tiled VAE for 81-frame decoding. |
| **LTX-Video (2.3/2.5)** | `ltx-video-2b-v0.9.safetensors` / distilled LoRAs | Built-in text / audio conditioning | ~10–14 GB | **Fast Real-Time DiT.** Fits entirely in VRAM. Supports single-stage distilled sampling and IC-LoRA motion guidance. |
| **HunyuanVideo** | `hunyuan_video_720_cfgdistill_fp8_e4m3fn.safetensors` or `Q4_K_M.gguf` | `llava` / `mllama` + `clip_l` (FP8) | ~18–22 GB | **Native PyTorch SDPA.** Blackwell `sm_120` runs scaled dot product attention without memory spikes. |

> [!TIP]
> **FP8 & GGUF vs FP16 Visual Fidelity:** On Blackwell 5th-generation Tensor Cores, FP8 (`e4m3fn`) and GGUF (`Q8_0`/`Q4_K_M`) quantization preserve practically indistinguishable image fidelity and text alignment compared to FP16, while cutting memory consumption by 40–60%. Keep FP16 reserved for enterprise GPUs with $\ge$ 48–96GB VRAM.

---

## 9. Curated Production Workflows

The repository includes a curated set of verified showcase workflows located in the [`workflows/`](workflows/) directory, automatically mounted into ComfyUI's native workflow browser (`/opt/ComfyUI/user/default/workflows`):

```text
workflows/
├── 01_WanVideo/            # Wan 2.1 Video Diffusion & ControlNet showcase
├── 03_LipSync_Portrait/    # LatentSync 1.5 audio-to-lip synchronization showcase
├── 06_IPAdapter/           # IP-Adapter Plus SDXL image conditioning & style transfer
└── README.md               # Guide to community workflows and upstream repositories
```

Simply open ComfyUI (`http://localhost:8188`), click **Workflows** in the top navigation, and select any workflow to load it immediately. Additional community workflows from upstream custom node repositories can be dropped directly into the `workflows/` directory.

---

## 10. Security, Supply Chain & Immutability

Production studios and homelabs require dependable security and predictable updates:

1. **Enterprise Container Vulnerability Scanning:**
   * Automated CI audits scan every container build with **Aqua Security Trivy**.
   * Validated with **0 Critical CVEs**.
   * Security reports are uploaded directly to the GitHub Security Tab via SARIF.
2. **Pillow 13 Source Build:**
   * Container builds Pillow 13 from source against Python 3.10 and `libjpeg-dev`, eliminating historical libpng/zlib vulnerabilities.
3. **Automated Supply Chain & Node Integrity Checks:**
   * [`scripts/audit_supply_chain_and_ai_security.py`](scripts/audit_supply_chain_and_ai_security.py) performs AST-based security analysis across custom nodes to detect unsanctioned network calls, malicious subprocess spawning, or prompt injection vectors.
4. **Strict Semantic Versioning & Immutability:**
   To guarantee exact reproducibility in production studio pipelines, all published images adhere to strict immutable versioning:
   * **Immutable Exact SemVer Tags (Never overwritten):**
     - `base`: `ghcr.io/talshmuli/comfyui-blackwell-bundle:v0.2.2-torch2.12.0.dev-cu128-base-YYYYMMDD-r<RUN_ID>`
     - `nodes`: `ghcr.io/talshmuli/comfyui-blackwell-bundle:v0.2.2-torch2.12.0.dev-cu128-nodes-YYYYMMDD-r<RUN_ID>`
     - `full`: `ghcr.io/talshmuli/comfyui-blackwell-bundle:v0.2.2-torch2.12.0.dev-cu128-full-YYYYMMDD-r<RUN_ID>`
     - `blender-worker`: `ghcr.io/talshmuli/comfyui-blackwell-bundle:blender4.4.3-cuda128-YYYYMMDD-r<RUN_ID>`
   * **Canonical Series Tags (Updated per stable release):**
     - `base-cuda128-sm120`
     - `nodes-cuda128-sm120` (alias `v0.2.2-cuda128-sm120`)
     - `full-cuda128-sm120`
     - `blender-worker`
   * **Latest Tag:**
     - `latest` points directly to the `nodes` production workstation.

---

## 11. Acknowledgements & Upstream Projects

* **[ComfyUI](https://github.com/comfyanonymous/ComfyUI)** by comfyanonymous — Modular node-based diffusion runtime.
* **[ai-dock/comfyui](https://github.com/ai-dock/comfyui)** by Rob Ballantyne — Multi-environment container architecture and process supervisor.
* **[PyTorch](https://github.com/pytorch/pytorch)** — Official nightly CUDA 12.8 builds with native Blackwell `sm_120` compute kernels.
* **[Blender](https://www.blender.org/)** — Headless 3D rigging, procedural animation, and AOV pass rendering.
* **[Smart ComfyUI Gallery](https://github.com/mmartial/smart-comfyui-gallery)** by mmartial — Digital asset management and workflow cataloging.
* **[ComfyUI-WanVideoWrapper](https://github.com/kijai/ComfyUI-WanVideoWrapper)** by Kijai — Wan 2.1 video diffusion wrapper.
* **[ComfyUI-LTXVideo](https://github.com/Lightricks/ComfyUI-LTXVideo)** by Lightricks — Real-time DiT video generation.
* **[ComfyUI-LivePortraitKJ](https://github.com/kijai/ComfyUI-LivePortraitKJ)** by Kijai — Facial reenactment.
* **[ComfyUI-LatentSyncWrapper](https://github.com/ShmuelRonen/ComfyUI-LatentSyncWrapper)** by Shmuel Ronen — Lip-sync animation.
* **[ComfyUI-AnimateDiff-Evolved](https://github.com/Kosinkadink/ComfyUI-AnimateDiff-Evolved)** by Kosinkadink — Motion modules.
* **[ComfyUI-VideoHelperSuite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite)** by Kosinkadink — Video processing utilities.
* **[ComfyUI-3D-Pack](https://github.com/MrForExample/ComfyUI-3D-Pack)** by MrForExample — 3D mesh and Gaussian splatting algorithms.
* **[ComfyUI-FL-YuE2](https://github.com/filliptm/ComfyUI-FL-YuE2)** by filliptm — AI song synthesis.
* **[Comfyui-Song-Generation-Suite](https://github.com/pmarmotte2/Comfyui-Song-Generation-Suite)** by pmarmotte2 — Music generation tools.
* **[ComfyUI-RVC](https://github.com/AIFSH/ComfyUI-RVC)** by AIFSH — Retrieval-based Voice Conversion.
* **[ComfyUI-GGUF](https://github.com/city96/ComfyUI-GGUF)** by City96 — High-performance quantized inference.
* **[ComfyUI_IPAdapter_plus](https://github.com/cubiq/ComfyUI_IPAdapter_plus)** by cubiq — Identity and style image prompting.
* **[comfyui_controlnet_aux](https://github.com/Fannovel16/comfyui_controlnet_aux)** by Fannovel16 — ControlNet preprocessors.
* **[ComfyUI-KJNodes](https://github.com/kijai/ComfyUI-KJNodes)** by Kijai — Workflow utilities.
* **[ComfyUI-Copilot](https://github.com/AIDC-AI/ComfyUI-Copilot)** by AIDC-AI — In-canvas workflow assistant.
* **[ComfyUI-BlenderAI-node](https://github.com/AIGODLIKE/ComfyUI-BlenderAI-node)** by AIGODLIKE — Blender integration bridge.

---

## 12. License

This project is licensed under the [MIT License](LICENSE). ComfyUI, PyTorch, Blender, and upstream packages are licensed under their respective open-source licenses.

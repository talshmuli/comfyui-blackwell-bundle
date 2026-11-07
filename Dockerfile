# ==============================================================================
# ComfyUI & Blender Docker Container Suite for NVIDIA Blackwell (RTX 5090 / 5080)
# Multi-Stage Matrix Architecture:
#   - base: ComfyUI Core + PyTorch Nightly CUDA 12.8 (sm_120) (~12 GB)
#   - nodes: Generative Video & Character Animation Stack (~16 GB)
#   - blender-worker: Lean Headless Blender 4.4 LTS OptiX/CUDA (~3.5 GB)
#   - full: All-In-One Monolith (ComfyUI + All Nodes + Blender 4.4 LTS) (~19 GB)
# ==============================================================================

# ==============================================================================
# Stage 1: Base - ComfyUI Core on PyTorch Nightly CUDA 12.8 (sm_120)
# Minimalist, clean ComfyUI core runtime without custom nodes (~12 GB)
# ==============================================================================
FROM ghcr.io/ai-dock/comfyui:latest-cuda AS base

LABEL maintainer="Tal Shmuli" \
      org.opencontainers.image.title="ComfyUI Blackwell Base (RTX 5090 / 5080)" \
      org.opencontainers.image.description="ComfyUI Core Docker Container for NVIDIA Blackwell RTX 5090 / 5080 (sm_120, CUDA 12.8)" \
      org.opencontainers.image.authors="Tal Shmuli <70902336+talshmuli@users.noreply.github.com>" \
      org.opencontainers.image.url="https://github.com/talshmuli/comfyui-blackwell-bundle" \
      org.opencontainers.image.source="https://github.com/talshmuli/comfyui-blackwell-bundle" \
      org.opencontainers.image.documentation="https://github.com/talshmuli/comfyui-blackwell-bundle/blob/master/README.md" \
      org.opencontainers.image.vendor="Tal Shmuli" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.base.name="ghcr.io/ai-dock/comfyui:latest-cuda"

# hadolint ignore=DL3002,DL3066
USER root

# Fix Hadolint DL4006: Set the SHELL option -o pipefail before RUN with pipes
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Apply official Ubuntu security updates, patch npm/tar, install libjpeg-dev for Pillow, and eliminate dormant daemons
# hadolint ignore=DL3008,DL3015,DL3016
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends libjpeg-dev && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /opt/caddy /opt/syncthing /usr/bin/cloudflared \
           /opt/environments/python/jupyter \
           /opt/environments/python/serviceportal \
           /opt/environments/python/api \
           /opt/environments/python/python_310 && \
    export PATH="/opt/nvm/versions/node/v22.2.0/bin:$PATH" && \
    npm install -g npm@10.9.9

# Install official PyTorch, torchvision, and torchaudio nightly builds compiled
# with native CUDA 12.8 and Blackwell sm_120 compute capability kernels.
RUN /opt/environments/python/comfyui/bin/pip install --no-cache-dir \
        --force-reinstall --no-deps --pre \
        torch torchvision torchaudio \
        --index-url https://download.pytorch.org/whl/nightly/cu128 && \
    /opt/environments/python/comfyui/bin/pip freeze | grep -E '^(torch|torchvision|torchaudio)==' > /opt/environments/python/comfyui/constraints.txt && \
    /opt/environments/python/comfyui/bin/pip install --no-cache-dir \
        nvidia-cufile-cu12 \
        nvidia-cusparselt-cu12 \
        nvidia-nvshmem-cu12 && \
    /opt/environments/python/comfyui/bin/pip install --no-cache-dir --upgrade \
        "nvidia-cuda-cupti-cu12>=12.8" \
        "nvidia-cudnn-cu12>=9.20" \
        "nvidia-cublas-cu12>=12.8" \
        "nvidia-cusolver-cu12>=11.7" \
        "nvidia-cuda-runtime-cu12>=12.8" \
        "nvidia-cuda-nvrtc-cu12>=12.8" \
        "nvidia-nccl-cu12>=2.29" && \
    /opt/environments/python/comfyui/bin/pip install --no-cache-dir \
        "pillow==11.1.0" && \
    /opt/environments/python/comfyui/bin/pip install --no-cache-dir --upgrade \
        "aiohttp>=3.13.4" \
        "pip>=24.0" \
        "setuptools>=70.0.0" \
        "jinja2>=3.1.5" \
        "gitpython>=3.1.44" \
        "pyjwt>=2.9.0" \
        "certifi>=2024.8.30" \
        "h11>=0.14.0" \
        "anyio>=4.6.0" && \
    /opt/environments/python/comfyui/bin/pip uninstall -y xformers

# Enforce pip constraints globally to prevent runtime custom node installs from downgrading PyTorch
ENV PIP_CONSTRAINT=/opt/environments/python/comfyui/constraints.txt

# Update ComfyUI core to latest upstream master to support modern custom nodes (comfy_api, Wan2.1, LTXVideo)
# Install modern ComfyUI master dependencies with --no-deps to protect cu128 PyTorch and prevent resolver backtracking
RUN git -C /opt/ComfyUI fetch --depth=1 origin master && \
    git -C /opt/ComfyUI checkout -f FETCH_HEAD && \
    /opt/environments/python/comfyui/bin/pip install --no-cache-dir \
        av && \
    /opt/environments/python/comfyui/bin/pip install --no-cache-dir --no-deps \
        "SQLAlchemy>=2.0.0" \
        alembic \
        simpleeval \
        blake3 \
        comfy-aimdo \
        comfy-kitchen \
        comfyui-frontend-package \
        comfyui-workflow-templates \
        comfyui-workflow-templates-json \
        comfyui-embedded-docs

# Copy verified default workflow ensuring immediate SD1.5 out-of-the-box UI functionality
COPY default_workflow.json /opt/ComfyUI/default_workflow.json
COPY scripts/preflight_model_alias.sh /opt/ai-dock/bin/preflight.d/20-model-alias.sh
RUN chmod +x /opt/ai-dock/bin/preflight.d/20-model-alias.sh

WORKDIR /workspace

# ==============================================================================
# Stage 2: Nodes - Generative Video & 3D Character Animation Stack (~16 GB)
# Adds verified video/portrait custom nodes and pinned ML dependencies
# ==============================================================================
FROM base AS nodes

LABEL maintainer="Tal Shmuli" \
      org.opencontainers.image.title="ComfyUI Blackwell Nodes (RTX 5090 / 5080)" \
      org.opencontainers.image.description="ComfyUI Production Nodes for NVIDIA Blackwell RTX 5090 / 5080 (sm_120, CUDA 12.8)"

# Fix Hadolint DL3003: Use WORKDIR to switch directories instead of cd
WORKDIR /opt/ComfyUI/custom_nodes

# Install system libraries for 3D processing, OpenGL rendering, headless GLSL, and audio I/O
# hadolint ignore=DL3008,DL3015
RUN apt-get update && apt-get install -y --no-install-recommends \
        libopengl0 \
        libgl1-mesa-glx \
        libglib2.0-0 \
        libportaudio2 && \
    rm -rf /var/lib/apt/lists/*

# Pre-install complete AI video, 3D, and music production custom node suite with network retry resilience
RUN clone_node() { \
        local url="$1"; \
        local commit="${2:-}"; \
        local dir; \
        dir="$(basename "$url" .git)"; \
        local max_attempts=3; \
        local attempt=1; \
        while [ "$attempt" -le "$max_attempts" ]; do \
            echo "Cloning $dir (attempt $attempt/$max_attempts)..."; \
            rm -rf "$dir"; \
            if [ -n "$commit" ]; then \
                if git clone "$url" "$dir" && git -C "$dir" checkout "$commit"; then \
                    return 0; \
                fi; \
            elif git clone --depth=1 "$url" "$dir"; then \
                return 0; \
            fi; \
            echo "Clone failed for $dir. Retrying in 3s..."; \
            rm -rf "$dir"; \
            sleep 3; \
            attempt=$((attempt + 1)); \
        done; \
        echo "Error: Failed to clone $dir after $max_attempts attempts." >&2; \
        return 1; \
    }; \
    export GIT_TERMINAL_PROMPT=0 && \
    clone_node https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git 593fcb07 && \
    clone_node https://github.com/kijai/ComfyUI-LivePortraitKJ.git && \
    clone_node https://github.com/ShmuelRonen/ComfyUI-LatentSyncWrapper.git && \
    clone_node https://github.com/Kosinkadink/ComfyUI-AnimateDiff-Evolved.git b3e508a && \
    clone_node https://github.com/MrForExample/ComfyUI-3D-Pack.git && \
    clone_node https://github.com/city96/ComfyUI-GGUF.git && \
    clone_node https://github.com/kijai/ComfyUI-WanVideoWrapper.git && \
    clone_node https://github.com/kijai/ComfyUI-KJNodes.git && \
    clone_node https://github.com/Fannovel16/ComfyUI-Frame-Interpolation.git && \
    clone_node https://github.com/cubiq/ComfyUI_IPAdapter_plus.git && \
    clone_node https://github.com/pmarmotte2/Comfyui-Song-Generation-Suite.git && \
    clone_node https://github.com/filliptm/ComfyUI-FL-YuE2.git && \
    clone_node https://github.com/AIFSH/ComfyUI-RVC.git && \
    clone_node https://github.com/Lightricks/ComfyUI-LTXVideo.git && \
    clone_node https://github.com/Fannovel16/comfyui_controlnet_aux.git && \
    clone_node https://github.com/AIDC-AI/ComfyUI-Copilot.git && \
    sed -i 's/from sqlalchemy.orm import identity/# from sqlalchemy.orm import identity/' ComfyUI-Copilot/backend/controller/conversation_api.py && \
    sed -i '1s/^/import os, sys\nglob_path = os.path.join(os.path.dirname(__file__), "glob")\nif glob_path not in sys.path:\n    sys.path.append(glob_path)\n/' ComfyUI-Manager/__init__.py

# Apply upstream compatibility patches for Blackwell sm_120 runtime and headless environments
COPY patches /opt/patches
RUN git -C ComfyUI-3D-Pack apply --ignore-whitespace /opt/patches/3d_pack.patch && \
    git -C ComfyUI-WanVideoWrapper apply --ignore-whitespace /opt/patches/wanvideo.patch && \
    git -C ComfyUI-RVC apply --ignore-whitespace /opt/patches/rvc.patch && \
    git -C ComfyUI-LTXVideo apply --ignore-whitespace /opt/patches/ltxvideo.patch && \
    git -C ComfyUI-VideoHelperSuite apply --ignore-whitespace /opt/patches/vhs.patch && \
    git -C ComfyUI-FL-YuE2 apply --ignore-whitespace /opt/patches/yue2.patch && \
    rm -rf /opt/patches

# Install Python dependencies for video generation, portrait animation, 3D, and music production,
# strictly protecting PyTorch nightly CUDA 12.8 Blackwell kernels from overwrite
RUN /opt/environments/python/comfyui/bin/pip install --no-cache-dir \
        "numpy<2.0.0,>=1.24.0" \
        "protobuf<5,>=4.25.3" \
        "onnx<1.16" \
        insightface \
        "huggingface-hub<1.0" \
        "transformers<4.50,>=4.47" \
        pykalman \
        "mediapipe<0.10.15" \
        moviepy \
        ffmpeg-python \
        pydub \
        pymeshlab \
        omegaconf \
        einops \
        onnxruntime-gpu \
        pyhocon \
        plyfile \
        trimesh \
        "sqlalchemy>=2.0.0" \
        python-dotenv \
        lazy_loader \
        objprint \
        varname \
        questionary \
        dataclasses-json \
        python-multipart \
        "packaging>=24.2" \
        "gguf>=0.13.0" \
        sentencepiece \
        ftfy \
        comfy_angle \
        PyOpenGL \
        PyOpenGL_accelerate \
        comfyui-workflow-templates-core \
        comfyui-workflow-templates-media-video \
        comfyui-workflow-templates-media-image \
        comfyui-workflow-templates-media-api \
        comfyui-workflow-templates-media-other \
        comfyui-workflow-templates-media-assets-01 \
        comfyui-workflow-templates-media-assets-02 && \
    /opt/environments/python/comfyui/bin/pip install --no-cache-dir --no-deps \
        "diffusers>=0.35.0" \
        "local-attention<=1.8.6" \
        importlib-metadata \
        tensorboardX \
        accelerate \
        lpips \
        torchmetrics \
        onnx2torch \
        facenet-pytorch \
        kiui && \
    /opt/environments/python/comfyui/bin/python -c "import kiui, pathlib; (pathlib.Path(kiui.__file__).parent / 'typing.py').write_text('from typing import *\nimport torch\nimport numpy as np\n\nTensor = torch.Tensor\nndarray = np.ndarray\n')" && \
    /opt/environments/python/comfyui/bin/pip install --no-cache-dir \
        "pillow==11.1.0" && \
    /opt/environments/python/comfyui/bin/pip install --no-cache-dir --upgrade \
        "aiohttp>=3.13.4" \
        "jinja2>=3.1.5"

WORKDIR /workspace

# ==============================================================================
# Stage 3: Blender-Worker - Dedicated Lean Headless Blender 4.4 LTS (~3.5 GB)
# OptiX/CUDA sm_120 rendering for procedural animation & pass generation
# ==============================================================================
FROM nvidia/cuda:12.8.0-base-ubuntu24.04 AS blender-worker

LABEL maintainer="Tal Shmuli" \
      org.opencontainers.image.title="Blender Worker (RTX 5090 / 5080)" \
      org.opencontainers.image.description="Blender 4.4 LTS Headless Worker for RTX 5090 Blackwell (CUDA 12.8, OptiX)" \
      org.opencontainers.image.authors="Tal Shmuli <70902336+talshmuli@users.noreply.github.com>" \
      org.opencontainers.image.url="https://github.com/talshmuli/comfyui-blackwell-bundle" \
      org.opencontainers.image.source="https://github.com/talshmuli/comfyui-blackwell-bundle" \
      org.opencontainers.image.documentation="https://github.com/talshmuli/comfyui-blackwell-bundle/blob/master/README.md" \
      org.opencontainers.image.vendor="Tal Shmuli" \
      org.opencontainers.image.licenses="MIT"

# Fix Hadolint DL4006: Set the SHELL option -o pipefail before RUN with pipes
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# hadolint ignore=DL3008,DL3015
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        xz-utils \
        git \
        python3 \
        libx11-6 \
        libxxf86vm1 \
        libxcursor1 \
        libxi6 \
        libxrandr2 \
        libxinerama1 \
        libgl1 \
        libegl1 \
        libsm6 \
        libxext6 \
        libxkbcommon0 \
        libdbus-1-3 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /opt/blender
RUN curl -sL "https://download.blender.org/release/Blender4.4/blender-4.4.3-linux-x64.tar.xz" | \
    tar -xJ -C /opt/blender --strip-components=1 && \
    ln -s /opt/blender/blender /usr/local/bin/blender && \
    mkdir -p /opt/blender/4.4/scripts/addons && \
    git clone --depth=1 https://github.com/AIGODLIKE/ComfyUI-BlenderAI-node.git /opt/blender/4.4/scripts/addons/ComfyUI-BlenderAI-node && \
    /opt/blender/4.4/python/bin/python3.11 -m pip install --no-cache-dir --upgrade certifi urllib3 requests setuptools pip

WORKDIR /workspace
RUN mkdir -p /workspace/scenes /workspace/passes /opt/scripts

COPY scripts/blender_runner.py /opt/scripts/blender_runner.py
COPY scripts/blender_entrypoint.sh /opt/scripts/blender_entrypoint.sh
RUN chmod +x /opt/scripts/blender_entrypoint.sh /opt/scripts/blender_runner.py

ENTRYPOINT ["/opt/scripts/blender_entrypoint.sh"]
CMD ["python3", "/opt/scripts/blender_runner.py"]

# ==============================================================================
# Stage 4: Full (Studio Monolith) - ComfyUI + All Nodes + Blender 4.4 LTS (~19 GB)
# All-In-One Studio VFX container with ComfyUI core, custom nodes, and Blender
# ==============================================================================
FROM nodes AS full

LABEL maintainer="Tal Shmuli" \
      org.opencontainers.image.title="ComfyUI Blackwell Full Studio (RTX 5090 / 5080)" \
      org.opencontainers.image.description="All-In-One ComfyUI & Blender 4.4 LTS VFX Studio for NVIDIA Blackwell RTX 5090 / 5080 (sm_120, CUDA 12.8)" \
      org.opencontainers.image.authors="Tal Shmuli <70902336+talshmuli@users.noreply.github.com>" \
      org.opencontainers.image.url="https://github.com/talshmuli/comfyui-blackwell-bundle" \
      org.opencontainers.image.source="https://github.com/talshmuli/comfyui-blackwell-bundle" \
      org.opencontainers.image.documentation="https://github.com/talshmuli/comfyui-blackwell-bundle/blob/master/README.md" \
      org.opencontainers.image.vendor="Tal Shmuli" \
      org.opencontainers.image.licenses="MIT"

# Fix Hadolint DL4006: Set the SHELL option -o pipefail before RUN with pipes
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# hadolint ignore=DL3008,DL3015
RUN apt-get update && apt-get install -y --no-install-recommends \
        libx11-6 \
        libxxf86vm1 \
        libxcursor1 \
        libxi6 \
        libxrandr2 \
        libxinerama1 \
        libgl1 \
        libegl1 \
        libsm6 \
        libxext6 \
        libxkbcommon0 \
        libdbus-1-3 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /opt/blender
RUN curl -sL "https://download.blender.org/release/Blender4.4/blender-4.4.3-linux-x64.tar.xz" | \
    tar -xJ -C /opt/blender --strip-components=1 && \
    ln -s /opt/blender/blender /usr/local/bin/blender && \
    mkdir -p /opt/blender/4.4/scripts/addons && \
    git clone --depth=1 https://github.com/AIGODLIKE/ComfyUI-BlenderAI-node.git /opt/blender/4.4/scripts/addons/ComfyUI-BlenderAI-node && \
    /opt/blender/4.4/python/bin/python3.11 -m pip install --no-cache-dir --upgrade certifi urllib3 requests setuptools pip

WORKDIR /workspace


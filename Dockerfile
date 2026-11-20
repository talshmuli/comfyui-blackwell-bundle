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

# Apply official Ubuntu security updates, install libjpeg-dev for Pillow, and eliminate dormant daemons and unused bundles
# hadolint ignore=DL3008,DL3015,DL3016
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends libjpeg-dev && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /opt/caddy /opt/syncthing /usr/bin/cloudflared \
           /opt/environments/python/jupyter \
           /opt/environments/python/serviceportal \
           /opt/environments/python/api \
           /opt/environments/python/python_310 \
           /usr/lib/python3.10/ensurepip/_bundled \
           /opt/nvm /root/.nvm && \
    mkdir -p /opt/nvm && \
    echo 'nvm() { :; }' > /opt/nvm/nvm.sh && \
    touch /opt/nvm/bash_completion && \
    ln -sf /opt/environments/python/comfyui/bin/python /usr/local/bin/python && \
    ln -sf /opt/environments/python/comfyui/bin/python /usr/bin/python

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
        "nvidia-nccl-cu12>=2.29" \
        "pip>=24.0" \
        "setuptools>=78.1.1" \
        "soupsieve>=2.8.4" \
        "fsspec>=2025.2.0" \
        "jupyter_core>=5.8.1" \
        "oauthlib>=4.0.0" \
        wheel \
        pybind11 && \
    mkdir -p /opt/wheels /tmp/pillow-build && \
    curl -sL "https://files.pythonhosted.org/packages/source/p/pillow/pillow-13.0.0.tar.gz" | tar -xz -C /tmp/pillow-build --strip-components=1 && \
    sed -i 's/requires-python = ">=3.11"/requires-python = ">=3.10"/' /tmp/pillow-build/pyproject.toml && \
    sed -i '/license/d' /tmp/pillow-build/pyproject.toml && \
    sed -i 's/setuptools>=77/setuptools/' /tmp/pillow-build/pyproject.toml && \
    /opt/environments/python/comfyui/bin/pip wheel --no-cache-dir --no-build-isolation --no-deps -w /opt/wheels /tmp/pillow-build && \
    /opt/environments/python/comfyui/bin/pip install --no-cache-dir --no-deps /opt/wheels/pillow-13.0.0-*.whl && \
    rm -rf /tmp/pillow-build && \
    /opt/environments/python/comfyui/bin/pip install --no-cache-dir --upgrade \
        "huggingface-hub<2.0,>=1.31.0" \
        "transformers>=5.20.2" \
        "onnx==1.21.0" \
        "opencv-python==4.11.0.86" \
        "opencv-python-headless>=4.10.0.84,<4.11.0" \
        "requests>=2.33.0" \
        "filelock>=3.20.3,<4.0.0" \
        "tornado>=6.6.1" \
        "idna>=3.15" \
        "python-dotenv>=1.2.2" \
        "gdown>=5.2.2" \
        "PyNaCl>=1.6.2" \
        "Pygments>=2.20.0" \
        "aiohttp>=3.13.4" \
        "jinja2>=3.1.5" \
        "httpcore>=1.0.7" \
        "h11>=0.16.0" \
        "gitpython>=3.1.44" \
        "pyjwt>=2.9.0" \
        "certifi>=2024.8.30" \
        "cryptography>=46.0.5" \
        "starlette>=0.40.0" \
        "urllib3>=2.3.0" && \
    find /opt/environments/python -name "*bom.cdx.json" -delete 2>/dev/null || true && \
    /opt/environments/python/comfyui/bin/pip uninstall -y xformers

# Enforce pip constraints globally to prevent runtime custom node installs from downgrading PyTorch
ENV PIP_CONSTRAINT=/opt/environments/python/comfyui/constraints.txt

# Update ComfyUI core to latest upstream master to support modern custom nodes (comfy_api, Wan2.1, LTXVideo)
# Install modern ComfyUI master dependencies with --no-deps to protect cu128 PyTorch and prevent resolver backtracking
COPY patches/comfy_path_resilience.patch /tmp/comfy_path_resilience.patch
RUN git -C /opt/ComfyUI fetch --depth=1 origin master && \
    git -C /opt/ComfyUI checkout -f FETCH_HEAD && \
    git -C /opt/ComfyUI apply --ignore-whitespace /tmp/comfy_path_resilience.patch && \
    rm -f /tmp/comfy_path_resilience.patch && \
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
        comfyui-embedded-docs && \
    sed -i '/self.app.router.add_get("\/templates\/{path:.*}", handler)/a \                self.app.router.add_get("/api/templates/{path:.*}", handler)' /opt/ComfyUI/server.py

# Copy verified default workflow ensuring immediate SD1.5 out-of-the-box UI functionality
COPY default_workflow.json /opt/ComfyUI/default_workflow.json
COPY scripts/preflight_model_alias.sh /opt/ai-dock/bin/preflight.d/20-model-alias.sh
COPY scripts/preflight_user_permissions.sh /opt/ai-dock/bin/preflight.d/25-user-permissions.sh
RUN chmod +x /opt/ai-dock/bin/preflight.d/20-model-alias.sh /opt/ai-dock/bin/preflight.d/25-user-permissions.sh

WORKDIR /workspace

# ==============================================================================
# Stage 2: Nodes - Generative Video & 3D Character Animation Stack (~16 GB)
# Adds verified video/portrait custom nodes and pinned ML dependencies
# ==============================================================================
FROM base AS nodes

LABEL maintainer="Tal Shmuli" \
      org.opencontainers.image.title="ComfyUI Blackwell Nodes (RTX 5090 / 5080)" \
      org.opencontainers.image.description="ComfyUI Production Nodes for NVIDIA Blackwell RTX 5090 / 5080 (sm_120, CUDA 12.8)"

# Fix Hadolint DL4006: Set the SHELL option -o pipefail before RUN with pipes
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Fix Hadolint DL3003: Use WORKDIR to switch directories instead of cd
WORKDIR /opt/ComfyUI/custom_nodes

# Install system libraries for 3D processing, OpenGL rendering, headless GLSL, and audio I/O
# hadolint ignore=DL3008,DL3015
RUN apt-get update && apt-get install -y --no-install-recommends \
        libopengl0 \
        libgl1-mesa-glx \
        libglib2.0-0 \
        libportaudio2 \
        libsndfile1 && \
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
    clone_node https://github.com/crystian/ComfyUI-Crystools.git && \
    clone_node https://github.com/kijai/ComfyUI-MelBandRoFormer.git && \
    clone_node https://github.com/filliptm/ComfyUI_FL-HeartMuLa.git && \
    clone_node https://github.com/ace-step/ACE-Step-ComfyUI.git && \
    clone_node https://github.com/Yuan-ManX/ComfyUI-Step1X-Edit.git && \
    clone_node https://github.com/ssitu/ComfyUI_UltimateSDUpscale.git && \
    clone_node https://github.com/ltdrdata/ComfyUI-Impact-Pack.git && \
    clone_node https://github.com/pythongosssss/ComfyUI-Custom-Scripts.git && \
    clone_node https://github.com/ltdrdata/ComfyUI-Inspire-Pack.git && \
    clone_node https://github.com/kijai/ComfyUI-DepthAnythingV2.git && \
    clone_node https://github.com/kijai/ComfyUI-Florence2.git && \
    clone_node https://github.com/kijai/ComfyUI-segment-anything-2.git && \
    clone_node https://github.com/evanspearman/ComfyMath.git && \
    clone_node https://github.com/kijai/ComfyUI-WanAnimatePreprocess.git && \
    clone_node https://github.com/kijai/ComfyUI-SCAIL-Pose.git && \
    clone_node https://github.com/yuvraj108c/ComfyUI-Video-Depth-Anything.git && \
    clone_node https://github.com/MinusZoneAI/ComfyUI-Kolors-MZ.git && \
    clone_node https://github.com/ClownsharkBatwing/RES4LYF.git && \
    clone_node https://github.com/edenartlab/eden_comfy_pipelines.git && \
    clone_node https://github.com/WASasquatch/was-node-suite-comfyui.git && \
    sed -i '1s/^/import os, sys\nglob_path = os.path.join(os.path.dirname(__file__), "glob")\nif glob_path not in sys.path:\n    sys.path.append(glob_path)\n/' ComfyUI-Manager/__init__.py && \
    git clone --depth 1 https://github.com/Coyote-A/ultimate-upscale-for-automatic1111.git /tmp/usdu && \
    cp -r /tmp/usdu/* ComfyUI_UltimateSDUpscale/repositories/ultimate_sd_upscale/ && \
    rm -rf /tmp/usdu && \
    printf '[default]\nsam_editor_cpu = False\nsam_editor_model = sam_vit_b_01ec64.pth\ncustom_wildcards = \ndisable_gpu_opencv = True\ngpu_gaussian_blur = False\nwildcard_cache_limit_mb = 50\n' > ComfyUI-Impact-Pack/impact-pack.ini && \
    find ComfyUI-LatentSyncWrapper -type f -exec sed -i 's/\r$//' {} + && \
    touch /root/.latentsync16_dependencies_installed

# Apply upstream compatibility patches for Blackwell sm_120 runtime and headless environments
COPY patches /opt/patches
RUN git -C ComfyUI-3D-Pack apply --ignore-whitespace /opt/patches/3d_pack.patch && \
    git -C ComfyUI-WanVideoWrapper apply --ignore-whitespace /opt/patches/wanvideo.patch && \
    git -C ComfyUI-RVC apply --ignore-whitespace /opt/patches/rvc.patch && \
    git -C ComfyUI-LTXVideo apply --ignore-whitespace /opt/patches/ltxvideo.patch && \
    git -C ComfyUI-VideoHelperSuite apply --ignore-whitespace /opt/patches/vhs.patch && \
    git -C ComfyUI-FL-YuE2 apply --ignore-whitespace /opt/patches/yue2.patch && \
    git -C ComfyUI-Step1X-Edit apply --ignore-whitespace /opt/patches/step1x.patch && \
    git -C ComfyUI-LatentSyncWrapper apply --ignore-whitespace /opt/patches/latentsync.patch && \
    rm -rf /opt/patches && \
    mkdir -p ComfyUI-RVC/rvc/assets/pretrained_v2 ComfyUI-RVC/rvc/assets/weights && \
    chmod -R 777 ComfyUI-RVC

# Install Python dependencies for video generation, portrait animation, 3D, and music production,
# strictly protecting PyTorch nightly CUDA 12.8 Blackwell kernels from overwrite
RUN /opt/environments/python/comfyui/bin/pip uninstall -y opencv-python opencv-contrib-python 2>/dev/null || true && \
    /opt/environments/python/comfyui/bin/pip install --no-cache-dir \
        "numpy<2.0.0,>=1.24.0" \
        "protobuf<5,>=4.25.3" \
        "onnx==1.21.0" \
        insightface \
        "huggingface-hub<2.0,>=1.31.0" \
        "transformers<5.21.0,>=5.10.0" \
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
        "sentencepiece>=0.2.1" \
        "rembg<=2.0.69" \
        "opencv-python-headless>=4.8.1.78,<4.11.0" \
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
        comfyui-workflow-templates-media-assets-02 \
        nvidia-ml-py \
        tbb \
        deepdiff \
        soundfile \
        librosa \
        piexif \
        segment-anything \
        dill \
        cachetools \
        webcolors \
        pywavelets && \
    /opt/environments/python/comfyui/bin/pip install --no-cache-dir --no-deps \
        "diffusers==0.38.0" \
        "local-attention<=1.8.6" \
        importlib-metadata \
        tensorboardX \
        accelerate \
        lpips \
        torchmetrics \
        onnx2torch \
        facenet-pytorch \
        kiui \
        faiss-cpu \
        tiktoken \
        pytorch-msssim \
        typing-inspection \
        pydantic-settings \
        pymcubes \
        xatlas \
        fast_simplification \
        torchtyping \
        jaxtyping \
        typeguard \
        fairseq \
        hydra-core \
        omegaconf \
        pyworld \
        torchcrepe \
        torchfcpe \
        praat-parselmouth \
        pyloudnorm \
        audioread \
        peft \
        resampy \
        soxr \
        py-cpuinfo \
        rotary-embedding-torch \
        qwen-vl-utils \
        liger-kernel \
        zipp \
        lightning-utilities \
        tomli \
        mako \
        "sympy>=1.13.3" && \
    /opt/environments/python/comfyui/bin/pip install --no-cache-dir --no-deps \
        pytorch-lightning && \
    /opt/environments/python/comfyui/bin/python -c "import kiui, pathlib; (pathlib.Path(kiui.__file__).parent / 'typing.py').write_text('from typing import *\nimport torch\nimport numpy as np\n\nTensor = torch.Tensor\nndarray = np.ndarray\n')" && \
    /opt/environments/python/comfyui/bin/pip install --no-cache-dir --force-reinstall --no-deps \
        /opt/wheels/pillow-13.0.0-*.whl && \
    find /opt/environments/python -name "*bom.cdx.json" -delete 2>/dev/null || true && \
    find /opt/ComfyUI/custom_nodes -name "*.py" -exec sed -i 's/logger\.warning("xFormers not available")/logger.debug("xFormers not available")/g' {} + && \
    find /opt/ComfyUI/custom_nodes -name "*.py" -exec sed -i 's/print("xFormers not available")/# print("xFormers not available")/g' {} + && \
    find /opt/ComfyUI/custom_nodes -name "*.py" -exec sed -i 's/logging\.warn("xFormers is not available/logging.debug("xFormers is not available/g' {} + && \
    sed -i 's/logger\.error(f"No motion models found/logger.info(f"No motion models found/' /opt/ComfyUI/custom_nodes/ComfyUI-AnimateDiff-Evolved/__init__.py && \
    chmod -R 777 /opt/ComfyUI/custom_nodes

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
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
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
RUN for attempt in 1 2 3 4 5; do \
        echo "Attempt $attempt: downloading Blender 4.4 LTS..." && \
        if curl -fsSL --retry 3 --retry-delay 2 -A "Mozilla/5.0" "https://download.blender.org/release/Blender4.4/blender-4.4.3-linux-x64.tar.xz" -o /tmp/blender.tar.xz || \
           curl -fsSL --retry 3 --retry-delay 2 -A "Mozilla/5.0" "https://mirrors.dotsrc.org/blender/release/Blender4.4/blender-4.4.3-linux-x64.tar.xz" -o /tmp/blender.tar.xz; then \
            tar -xJ -f /tmp/blender.tar.xz -C /opt/blender --strip-components=1 && \
            rm -f /tmp/blender.tar.xz && break; \
        fi; \
        echo "Attempt $attempt failed. Retrying in 5 seconds..." >&2; \
        sleep 5; \
    done && test -x /opt/blender/blender && \
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

COPY --from=blender-worker /opt/blender /opt/blender
RUN ln -s /opt/blender/blender /usr/local/bin/blender

WORKDIR /workspace


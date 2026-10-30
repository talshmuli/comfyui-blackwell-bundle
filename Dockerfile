# ==============================================================================
# ComfyUI Docker Container for NVIDIA GeForce RTX 5090 / 5080 (Blackwell sm_120)
# Base Image: Formal ai-dock/comfyui upstream on GitHub Container Registry (GHCR)
# ==============================================================================

FROM ghcr.io/ai-dock/comfyui:latest-cuda

LABEL maintainer="Tal Shmuli" \
      org.opencontainers.image.title="ComfyUI Blackwell (RTX 5090 / 5080)" \
      org.opencontainers.image.description="ComfyUI Docker Container for NVIDIA Blackwell RTX 5090 / 5080 (sm_120, CUDA 12.8)" \
      org.opencontainers.image.authors="Tal Shmuli <70902336+talshmuli@users.noreply.github.com>" \
      org.opencontainers.image.url="https://github.com/talshmuli/comfyui-blackwell-docker" \
      org.opencontainers.image.source="https://github.com/talshmuli/comfyui-blackwell-docker" \
      org.opencontainers.image.documentation="https://github.com/talshmuli/comfyui-blackwell-docker/blob/master/README.md" \
      org.opencontainers.image.vendor="Tal Shmuli" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.base.name="ghcr.io/ai-dock/comfyui:latest-cuda"

USER root

# Install official PyTorch, torchvision, and torchaudio nightly builds compiled
# with native CUDA 12.8 and Blackwell sm_120 compute capability kernels.
RUN /opt/environments/python/comfyui/bin/pip install --no-cache-dir \
        --force-reinstall --no-deps --pre \
        torch torchvision torchaudio \
        --index-url https://download.pytorch.org/whl/nightly/cu128 && \
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
    /opt/environments/python/comfyui/bin/pip uninstall -y xformers

# ==============================================================================
# Human Video Animation, Dialogue & Lip-Sync Baseline Custom Nodes & Packages
# ==============================================================================

# Pre-install baseline custom nodes:
# 1. VideoHelperSuite: Essential video ingestion, extraction, and mastering pipeline
# 2. LivePortraitKJ: Real-time expressive facial animation, micro-expressions, eye contact
# 3. LatentSyncWrapper: High-fidelity audio-conditioned latent phoneme lip-sync
RUN cd /opt/ComfyUI/custom_nodes && \
    git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git && \
    (cd ComfyUI-VideoHelperSuite && git checkout 593fcb07) && \
    git clone --depth=1 https://github.com/kijai/ComfyUI-LivePortraitKJ.git && \
    git clone --depth=1 https://github.com/ShmuelRonen/ComfyUI-LatentSyncWrapper.git

# Install Python dependencies for video generation and portrait animation,
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
        av \
        omegaconf \
        einops \
        onnxruntime-gpu && \
    /opt/environments/python/comfyui/bin/pip install --no-cache-dir --no-deps \
        diffusers \
        accelerate \
        lpips \
        torchmetrics \
        onnx2torch \
        facenet-pytorch

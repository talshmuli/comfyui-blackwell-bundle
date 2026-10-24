# ==============================================================================
# ComfyUI Docker Container for NVIDIA GeForce RTX 5090 / 5080 (Blackwell sm_120)
# Base Image: Formal ai-dock/comfyui upstream on GitHub Container Registry (GHCR)
# ==============================================================================

FROM ghcr.io/ai-dock/comfyui:latest-cuda

LABEL maintainer="Tal Shmuli" \
      org.opencontainers.image.title="ComfyUI Blackwell (RTX 5090 / 5080)" \
      org.opencontainers.image.description="ComfyUI Docker Container for NVIDIA Blackwell RTX 5090 / 5080 (sm_120, CUDA 12.8)" \
      org.opencontainers.image.source="https://github.com/talshmuli/comfyui-blackwell-docker" \
      org.opencontainers.image.url="https://github.com/talshmuli/comfyui-blackwell-docker" \
      org.opencontainers.image.licenses="MIT"

USER root

# Install official PyTorch and torchvision nightly builds compiled with native
# CUDA 12.8 and Blackwell sm_120 compute capability kernels.
RUN /opt/environments/python/comfyui/bin/pip install --no-cache-dir \
        --force-reinstall --no-deps --pre \
        torch torchvision \
        --index-url https://download.pytorch.org/whl/nightly/cu128 && \
    /opt/environments/python/comfyui/bin/pip install --no-cache-dir \
        nvidia-cufile-cu12 \
        nvidia-cusparselt-cu12 \
        nvidia-nvshmem-cu12 && \
    /opt/environments/python/comfyui/bin/pip install --no-cache-dir --upgrade \
        "nvidia-cuda-cupti-cu12>=12.8" \
        "nvidia-cudnn-cu12>=9.20" \
        "nvidia-cublas-cu12>=12.8" \
        "nvidia-cuda-runtime-cu12>=12.8" \
        "nvidia-cuda-nvrtc-cu12>=12.8" \
        "nvidia-nccl-cu12>=2.29" && \
    /opt/environments/python/comfyui/bin/pip uninstall -y xformers

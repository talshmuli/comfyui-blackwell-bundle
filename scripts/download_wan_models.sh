#!/usr/bin/env bash
# ==============================================================================
# Wan 2.2 / 2.1 Model Downloader for ComfyUI
# Downloads weights directly into host storage mounted to ComfyUI
# ==============================================================================
set -euo pipefail

MODELS_DIR="${1:-${COMFYUI_MODELS_PATH:-./data/models}}"

echo "=========================================================="
echo " Downloading Wan 2.2 / 2.1 Models into: ${MODELS_DIR}"
echo "=========================================================="

mkdir -p "${MODELS_DIR}/text_encoders"
mkdir -p "${MODELS_DIR}/vae"
mkdir -p "${MODELS_DIR}/diffusion_models"
mkdir -p "${MODELS_DIR}/controlnet/wan2.2-ti2v-5b-controlnet-depth-v1"

# 1. T5 Text Encoder (~10.5 GB)
echo "[1/4] Downloading umt5-xxl-enc-bf16.safetensors..."
wget -c --show-progress -O "${MODELS_DIR}/text_encoders/umt5-xxl-enc-bf16.safetensors" \
    "https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/umt5-xxl-enc-bf16.safetensors"

# 2. Wan 2.2 VAE (~1.4 GB)
echo "[2/4] Downloading Wan2_2_VAE_bf16.safetensors..."
wget -c --show-progress -O "${MODELS_DIR}/vae/Wan2_2_VAE_bf16.safetensors" \
    "https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/Wan2_2_VAE_bf16.safetensors"

# 3. FastWan 5B Diffusion Checkpoint (~10.5 GB)
echo "[3/4] Downloading Wan2_2-TI2V-5B-FastWanFullAttn_bf16.safetensors..."
wget -c --show-progress -O "${MODELS_DIR}/diffusion_models/Wan2_2-TI2V-5B-FastWanFullAttn_bf16.safetensors" \
    "https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/FastWan/Wan2_2-TI2V-5B-FastWanFullAttn_bf16.safetensors"

# 4. Depth ControlNet (~1.5 GB)
echo "[4/4] Downloading Depth ControlNet diffusion_pytorch_model.safetensors..."
wget -c --show-progress -O "${MODELS_DIR}/controlnet/wan2.2-ti2v-5b-controlnet-depth-v1/diffusion_pytorch_model.safetensors" \
    "https://huggingface.co/TheDenk/wan2.2-ti2v-5b-controlnet-depth-v1/resolve/main/diffusion_pytorch_model.safetensors"

echo "=========================================================="
echo " All Wan models downloaded successfully!"
echo " In ComfyUI, click 'Refresh' or reload the browser tab."
echo "=========================================================="

#!/bin/bash
# Automatically create cross-platform model aliases, subfolder mirrors, and starter media assets

CKPT_DIR="/opt/ComfyUI/models/checkpoints"
VAE_DIR="/opt/ComfyUI/models/vae"
DIFF_DIR="/opt/ComfyUI/models/diffusion_models"
INPUT_DIR="/opt/ComfyUI/input"

# 1. Default Checkpoint Alias (e.g. DreamShaper -> v1-5-pruned-emaonly)
TARGET="${DEFAULT_CHECKPOINT_ALIAS:-DreamShaper_8_pruned.safetensors}"
ALIAS="${DEFAULT_CHECKPOINT_NAME:-v1-5-pruned-emaonly.safetensors}"
if [ "$TARGET" != "none" ] && [ -d "$CKPT_DIR" ]; then
    if [ -f "$CKPT_DIR/$TARGET" ] && [ ! -e "$CKPT_DIR/$ALIAS" ]; then
        echo "[Preflight] Linking default checkpoint alias: $ALIAS -> $TARGET"
        ln -sf "$TARGET" "$CKPT_DIR/$ALIAS"
    fi
fi

# 2. Checkpoint Subfolder Mirroring (e.g. sd15/ -> root models)
if [ -d "$CKPT_DIR" ]; then
    mkdir -p "$CKPT_DIR/sd15"
    for f in "$CKPT_DIR"/*.safetensors "$CKPT_DIR"/*.ckpt; do
        [ -f "$f" ] || continue
        base=$(basename "$f")
        [ -e "$CKPT_DIR/sd15/$base" ] || ln -sf "../$base" "$CKPT_DIR/sd15/$base"
        # Also alias .ckpt to .safetensors if requested by legacy workflows
        stem="${base%.*}"
        [ -e "$CKPT_DIR/sd15/${stem}.ckpt" ] || ln -sf "../$base" "$CKPT_DIR/sd15/${stem}.ckpt"
    done
fi

# 3. VAE Subfolder Mirroring (e.g. wanvideo/ -> root VAEs)
if [ -d "$VAE_DIR" ]; then
    mkdir -p "$VAE_DIR/wanvideo"
    for f in "$VAE_DIR"/*.safetensors "$VAE_DIR"/*.pt "$VAE_DIR"/*.bin; do
        [ -f "$f" ] || continue
        base=$(basename "$f")
        [ -e "$VAE_DIR/wanvideo/$base" ] || ln -sf "../$base" "$VAE_DIR/wanvideo/$base"
    done
fi

# 4. Diffusion Models Subfolder Mirroring (e.g. WanVideo/2_2/ -> root diffusion models)
if [ -d "$DIFF_DIR" ]; then
    mkdir -p "$DIFF_DIR/WanVideo/2_2"
    for f in "$DIFF_DIR"/*.safetensors "$DIFF_DIR"/*.gguf; do
        [ -f "$f" ] || continue
        base=$(basename "$f")
        [ -e "$DIFF_DIR/WanVideo/$base" ] || { mkdir -p "$DIFF_DIR/WanVideo"; ln -sf "../$base" "$DIFF_DIR/WanVideo/$base"; }
        [ -e "$DIFF_DIR/WanVideo/2_2/$base" ] || ln -sf "../../$base" "$DIFF_DIR/WanVideo/2_2/$base"
    done
fi

# 5. Default Media Fallback Assets
if [ -d "$INPUT_DIR" ]; then
    # Starter 16-bit PCM WAV audio for LoadAudio nodes
    if [ ! -f "$INPUT_DIR/example.wav" ]; then
        /opt/environments/python/comfyui/bin/python -c "
import wave, struct
with wave.open('$INPUT_DIR/example.wav', 'w') as f:
    f.setnchannels(1); f.setsampwidth(2); f.setframerate(16000)
    f.writeframes(struct.pack('<' + ('h'*16000), *([0]*16000)))
" 2>/dev/null || true
    fi
    [ -e "$INPUT_DIR/talk.wav" ] || ln -sf "example.wav" "$INPUT_DIR/talk.wav"

    # Starter image alias for LoadImage nodes
    if [ ! -e "$INPUT_DIR/input_image.png" ]; then
        for img in "$INPUT_DIR"/*.png "$INPUT_DIR"/*.jpg; do
            if [ -f "$img" ]; then
                ln -sf "$(basename "$img")" "$INPUT_DIR/input_image.png"
                break
            fi
        done
    fi

    # Starter YuE2 training dataset pairs
    mkdir -p "$INPUT_DIR/yue2_pairs/source" "$INPUT_DIR/yue2_pairs/target"
    if [ -f "$INPUT_DIR/example.wav" ] && [ ! -f "$INPUT_DIR/yue2_pairs/source/sample.wav" ]; then
        cp "$INPUT_DIR/example.wav" "$INPUT_DIR/yue2_pairs/source/sample.wav"
        cp "$INPUT_DIR/example.wav" "$INPUT_DIR/yue2_pairs/target/sample.wav"
    fi
fi

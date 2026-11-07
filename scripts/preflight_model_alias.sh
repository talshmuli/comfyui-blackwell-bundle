#!/bin/bash
# Automatically create compatibility symlink if enabled and target exists
TARGET="${DEFAULT_CHECKPOINT_ALIAS:-DreamShaper_8_pruned.safetensors}"
ALIAS="${DEFAULT_CHECKPOINT_NAME:-v1-5-pruned-emaonly.safetensors}"
CKPT_DIR="/opt/ComfyUI/models/checkpoints"

if [ "$TARGET" != "none" ] && [ -d "$CKPT_DIR" ]; then
    if [ -f "$CKPT_DIR/$TARGET" ] && [ ! -e "$CKPT_DIR/$ALIAS" ]; then
        echo "[Preflight] Linking default checkpoint alias: $ALIAS -> $TARGET"
        ln -sf "$TARGET" "$CKPT_DIR/$ALIAS"
    fi
fi

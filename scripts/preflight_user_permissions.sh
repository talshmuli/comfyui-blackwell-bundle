#!/bin/bash
# Ensure /opt/ComfyUI/user is writable by non-root user even after volume mounts
mkdir -p /opt/ComfyUI/user/default
chown -R user:ai-dock /opt/ComfyUI/user
chmod -R 775 /opt/ComfyUI/user

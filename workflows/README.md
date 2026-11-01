# Curated Production Workflows

This directory is mounted directly into ComfyUI's user workflow folder (`/opt/ComfyUI/user/default/workflows`) when using `docker-compose.yml`. Workflows placed here appear immediately in ComfyUI's native workflow browser.

## Verified Showcase Templates

The workflows included in this directory are verified to load with 0 missing nodes in `comfyui-blackwell-bundle`:

| Directory | Showcase Workflow | Primary Nodes / Models |
|---|---|---|
| [`01_WanVideo/`](01_WanVideo/) | `wanvideo_2_2_5B_T2V_controlnet_example.json` | Wan 2.1 Video Diffusion, Video Combine, ControlNet |
| [`03_LipSync_Portrait/`](03_LipSync_Portrait/) | `latentsync1.5_comfyui_basic.json` | LatentSync 1.5 Audio-to-Lip synchronization |
| [`06_IPAdapter/`](06_IPAdapter/) | `ipadapter_advanced.json` | IP-Adapter Plus SDXL image conditioning & style transfer |

## Upstream Community Workflows

For experimental or model-specific pipelines, example workflows from custom node developers can be downloaded from the respective upstream repositories:

- **Wan 2.1 Video Wrapper:** [kijai/ComfyUI-WanVideoWrapper/examples](https://github.com/kijai/ComfyUI-WanVideoWrapper/tree/main/examples)
- **LTX-Video:** [Lightricks/ComfyUI-LTXVideo/examples](https://github.com/Lightricks/ComfyUI-LTXVideo/tree/master/examples)
- **LivePortrait & KJNodes:** [Kijai/ComfyUI-LivePortraitKJ/examples](https://github.com/Kijai/ComfyUI-LivePortraitKJ/tree/main/examples)
- **Song Generation Suite:** [pmarmotte2/Comfyui-Song-Generation-Suite/examples](https://github.com/pmarmotte2/Comfyui-Song-Generation-Suite/tree/main/examples)
- **3D Pack:** [MrForExample/ComfyUI-3D-Pack/_Example_Workflows](https://github.com/MrForExample/ComfyUI-3D-Pack/tree/main/_Example_Workflows)
- **IPAdapter Plus:** [cubiq/ComfyUI_IPAdapter_plus/examples](https://github.com/cubiq/ComfyUI_IPAdapter_plus/tree/main/examples)

> [!TIP]
> You can drop any `.json` or `.png` workflow into this folder on your host machine, and it will be immediately available in the ComfyUI browser without restarting the container.

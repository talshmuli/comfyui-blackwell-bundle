# Contributing to ComfyUI Blackwell Docker

Thank you for your interest in improving the ComfyUI Blackwell Docker build!

## How This Project Works
This repository provides automated build pipelines and Docker configurations tailored specifically for **NVIDIA Blackwell GeForce RTX 5090 and 5080 (`sm_120`)** GPUs running CUDA 12.8+.

* **Automated Builds:** GitHub Actions builds images bi-weekly (1st and 15th) via `.github/workflows/build.yml`.
* **Smart Change Detection:** Automated workflows check for upstream `ai-dock/comfyui` base updates and PyTorch nightly `cu128` releases before triggering builds.
* **Testing First:** Every build executes a CPU-safe validation suite ensuring PyTorch CUDA 12.8 runtime, `sm_120` compilation flags, Torchvision ops, and ComfyUI imports before pushing to GHCR.

## Submitting Pull Requests
1. Fork the repository and create your branch from `master`.
2. Keep changes focused and documented.
3. Test the Dockerfile locally:
   ```bash
   DOCKER_BUILDKIT=1 docker build --target nodes -t test-comfyui:build -f Dockerfile .
   ```
4. Run the validation suite locally:
   Launch an isolated test container on port `8190` (leaving production port `8188` uninterrupted) and execute the comprehensive integrity test:
   ```bash
   # Run isolated container
   docker run --rm -d --name comfyui-isolated-test \
     --gpus all \
     --shm-size 16gb \
     -p 8190:8188 \
     -e PUID=1000 -e PGID=1000 \
     -e COMFYUI_PORT_LOCAL=8188 \
     -e WEB_ENABLE_AUTH=false \
     test-comfyui:build

   # Execute the container integrity verification script:
   python3 scripts/validate_image.py --port 8190

   # Or run directly inside the container:
   docker exec comfyui-isolated-test /opt/environments/python/comfyui/bin/python /opt/scripts/validate_image.py

   # Stop and clean up the container
   docker stop comfyui-isolated-test
   ```

### Release Gatekeeper Audit Checks
All pull requests must pass the 6 release gatekeeper audit checks before merging:
1. **Zero Private Host Path Leaks:** No hardcoded private host paths (e.g. `/home/<user>` or `/mnt/...`) or personal environment variables in any tracked files or commit metadata.
2. **Workflow Sanitization:** All curated workflows in `workflows/` must be sanitized of machine-specific absolute paths, private model directories, and personal metadata.
3. **Clean Git History:** Full commit history must remain clean of personal leaks, credentials, or sensitive test data.
4. **Git Isolation Patterns:** `.gitignore` must properly isolate local environment overrides, personal workflows, and test outputs.
5. **Container Security & Supply Chain:** Zero critical vulnerabilities, Pillow 13.0.0 patched release maintained, strict `/bin/bash` shell enforcement, and permanent exclusion of telemetry/insecure extensions (such as `ComfyUI-Copilot`).
6. **Blackwell sm_120 Node Verification:** All 21 custom nodes in `custom_nodes.json` must load cleanly with zero `ImportError` or traceback logs during `validate_image.py` execution.

5. Submit your PR against `master` with a clear description of the motivation and verification output.

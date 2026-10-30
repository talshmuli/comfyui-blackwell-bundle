# Multi-Tier Docker Image Matrix & Blender Worker Implementation Plan

> **Goal:** Transform `comfyui-blackwell-docker` into an enterprise 4-tier build matrix (`base`, `nodes`, `blender-worker`, `full`) with modular Docker Compose orchestration, verified local testing on isolated ports, and expanded one-stop-shop studio documentation.

**User Constraints:**
* Zero impact to the user's active `comfyui` container currently in use on port `8188`.
* All modifications staged on branch `feat/matrix-builds-blender-worker`.
* Full local validation of build targets and Docker Compose inter-service communication before any remote commit/push.

---

## Proposed Changes & File Structure

### Repository: `talshmuli/comfyui-blackwell-docker`

| File | Primary Responsibility |
| :--- | :--- |
| `Dockerfile` | Multi-stage build defining targets: `base`, `nodes`, `blender-worker`, and `full`. |
| `docker-compose.yml` | Multi-profile compose orchestration supporting `modular` (`nodes` + `blender-worker`), `full`, and `base`. |
| `.github/workflows/build.yml` | GitHub Actions parallel matrix workflow building, testing, and publishing all 4 targets with Trivy & CodeQL v4. |
| `README.md` | Comprehensive documentation including tier specifications, compose guide, and one-stop shop studio rationale. |

---

## Detailed Task Breakdown

### Task 1: Multi-Stage `Dockerfile` Refactoring
- **Goal:** Structure `Dockerfile` into 4 distinct target stages:
  - `base`: Upstream ai-dock base + PyTorch Nightly CUDA 12.8 sm_120 + CUDA runtime.
  - `nodes`: Inherits `base` + VideoHelperSuite, LivePortraitKJ, LatentSyncWrapper, AnimateDiff-Evolved, ComfyUI-3D-Pack, pinned dependencies.
  - `blender-worker`: Standalone lean Ubuntu stage + Blender 4.4.3 LTS + ComfyUI-BlenderAI-node addon + entrypoint runner.
  - `full`: Inherits `nodes` + adds Blender 4.4.3 layer.
- **Verification:** Run Dockerfile linting (`hadolint` syntax check) and verify stage syntax.

### Task 2: Local Test Builds & Integrity Checks
- **Goal:** Build and verify all 4 stages locally using isolated test tags:
  - `docker build --target base -t test-comfyui:base .`
  - `docker build --target nodes -t test-comfyui:nodes .`
  - `docker build --target blender-worker -t test-comfyui:blender .`
  - `docker build --target full -t test-comfyui:full .`
- **Verification:**
  - `test-comfyui:base`: Verify `sm_120` in torch build config; verify registered nodes count equals clean ComfyUI core (~100 nodes).
  - `test-comfyui:nodes`: Verify all custom nodes import without error (0 missing modules, 0 crashes).
  - `test-comfyui:blender`: Verify `blender -b --version` outputs Blender 4.4.3.
  - `test-comfyui:full`: Verify both ComfyUI nodes and Blender binary coexist cleanly.

### Task 3: Multi-Profile `docker-compose.yml` & Inter-Service Testing
- **Goal:** Implement Compose profiles:
  - Profile `modular` (default): `comfyui` (`nodes`) + `blender-worker` on bridge `vfx-net` with shared volume `passes_bus`.
  - Profile `full`: `comfyui-full`.
  - Profile `base`: `comfyui-base`.
- **Verification:**
  - Launch modular profile on non-colliding test port (`8189:8188`) using project name `test-compose`:
    `docker compose -p test-compose --profile modular up -d`
  - Verify `blender-worker` can reach `http://comfyui:8188/system_stats` over `vfx-net`.
  - Verify a file written to `/workspace/passes` in `blender-worker` is instantly visible at `/opt/ComfyUI/input/passes` in `comfyui`.
  - Teardown: `docker compose -p test-compose --profile modular down -v`.

### Task 4: GitHub Actions Parallel Matrix Workflow (`build.yml`)
- **Goal:** Update CI workflow to build all 4 targets in parallel:
  - Matrix: `[base, nodes, blender-worker, full]`
  - Each target runs appropriate unit checks.
  - Generates Trivy SARIF report per target.
  - Uploads to GitHub Security tab via `github/codeql-action/upload-sarif@v4`.
  - Uploads downloadable zip artifact via `actions/upload-artifact@v4`.
  - Tags images with SemVer and canonical tag (e.g., `ghcr.io/...:nodes-cuda128-sm120`).

### Task 5: Documentation & One-Stop Shop Rationale
- **Goal:** Update `README.md`:
  - 4-Tier Matrix comparison table.
  - Quickstart guide for `nodes + blender-worker` microservices.
  - Expanded rationale explaining why a unified containerized studio layer eliminates dependency hell and accelerates Blackwell RTX 5090 production.

---

## Execution Constraints Checklist
- [ ] Do NOT stop, restart, or kill the active `comfyui` container on port 8188.
- [ ] Always use custom test ports (e.g., 8189) during local Compose checks.
- [ ] Verify 100% test pass locally before pushing to GitHub remote.

from pathlib import Path

def test_stage2_cleans_and_locks():
    content = Path("Dockerfile").read_text()
    stage2 = content.split("FROM base AS nodes")[1].split("FROM nvidia/cuda:12.8.0-base-ubuntu24.04 AS blender-worker")[0]
    
    # Assert Stage 2 keeps node-specific packages and final cleanup
    assert 'pytorch-lightning' in stage2
    assert 'kiui' in stage2
    assert '*bom.cdx.json' in stage2

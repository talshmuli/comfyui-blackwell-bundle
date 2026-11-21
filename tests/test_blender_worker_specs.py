from pathlib import Path

def test_blender_worker_security_specs():
    content = Path("Dockerfile").read_text()
    stage3 = content.split("AS blender-worker")[1].split("FROM nodes AS full")[0]
    
    # Assert upgraded setuptools, idna, requests and SBOM deletion in blender python
    assert 'setuptools>=84.2.1' in stage3
    assert 'idna>=3.15' in stage3
    assert 'requests>=2.33.0' in stage3
    assert 'find /opt/blender -name "*bom.cdx.json" -delete' in stage3

def test_stage4_cleans_blender_sbom():
    content = Path("Dockerfile").read_text()
    stage4 = content.split("FROM nodes AS full")[1]
    assert 'find /opt/blender -name "*bom.cdx.json" -delete' in stage4

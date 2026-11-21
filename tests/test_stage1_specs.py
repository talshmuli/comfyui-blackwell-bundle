import re
from pathlib import Path

def test_stage1_has_cascaded_security_packages():
    content = Path("Dockerfile").read_text()
    stage1 = content.split("FROM base AS nodes")[0]
    
    # Assert upgraded packages exist in Stage 1
    assert 'requests>=2.33.0' in stage1
    assert 'filelock>=3.20.3' in stage1
    assert 'tornado>=6.5.10' in stage1
    assert 'idna>=3.15' in stage1
    assert 'python-dotenv>=1.2.2' in stage1
    assert 'gdown>=5.2.2' in stage1
    assert 'PyNaCl>=1.6.2' in stage1
    assert 'Pygments>=2.20.0' in stage1
    assert 'h11>=0.16.0' in stage1
    assert 'httpcore>=1.0.7' in stage1
    assert 'transformers>=5.20.2' in stage1
    assert 'onnx==1.21.0' in stage1
    assert '*bom.cdx.json' in stage1

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setenv('MATILDA_DB', str(tmp_path / 'test.db'))
    monkeypatch.setenv('MATILDA_CACHE_TTL', '999999999')
    with TestClient(app) as client:
        yield client

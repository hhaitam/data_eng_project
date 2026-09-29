import hashlib
from pathlib import Path
import pytest
import requests

from dvf_elt.ingest.download import download_file

class FakeResponse:
    def __init__(self, content: bytes):
        self._content = content
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def raise_for_status(self): pass
    def iter_content(self, chunk_size):
        yield self._content

def test_download_file_writes_content_and_returns_correct_sha(tmp_path, monkeypatch):
    payload = b"fake dvf csv content"
    monkeypatch.setattr(requests, "get", lambda *a, **k: FakeResponse(payload))

    dest = tmp_path / "out.csv"
    sha = download_file("http://example.invalid/fake.csv", dest)

    assert dest.read_bytes() == payload
    assert sha == hashlib.sha256(payload).hexdigest()
    assert not dest.with_suffix(".csv.part").exists()
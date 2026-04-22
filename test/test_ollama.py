import requests
import pytest

OLLAMA_URL = "http://localhost:11434"
MODEL = "gemma4:e4b"

def test_ollama_interaction():
    # Check connection and tags
    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        resp.raise_for_status()
    except requests.ConnectionError:
        pytest.fail(f"Cannot connect to Ollama at {OLLAMA_URL}")

    models = [m["name"] for m in resp.json().get("models", [])]
    assert any(MODEL in m for m in models), f"Model '{MODEL}' not found in {models}"

    # Check generation
    resp = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={"model": MODEL, "prompt": "Say hello in one sentence.", "stream": False},
        timeout=60,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "response" in data
    assert len(data["response"]) > 0
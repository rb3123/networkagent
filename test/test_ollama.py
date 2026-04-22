import requests

OLLAMA_URL = "http://localhost:11434"
MODEL = "gemma4:e4b"


def test_connection():
    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        resp.raise_for_status()
        models = [m["name"] for m in resp.json().get("models", [])]
        print(f"Ollama is running. Available models: {models}")

        if not any(MODEL in m for m in models):
            print(f"WARNING: '{MODEL}' not found in available models.")
            return
    except requests.ConnectionError:
        print(f"ERROR: Cannot connect to Ollama at {OLLAMA_URL}. Is it running?")
        return

    resp = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={"model": MODEL, "prompt": "Say hello in one sentence.", "stream": False},
        timeout=60,
    )
    resp.raise_for_status()
    print(f"Response from {MODEL}: {resp.json()['response']}")


if __name__ == "__main__":
    test_connection()

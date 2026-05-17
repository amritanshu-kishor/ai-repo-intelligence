"""
Quick Hugging Face connectivity check.
Run from repo-ai/:  python test_hf.py
"""

import json
import sys

import requests
from requests.exceptions import JSONDecodeError

from config import HF_API_TOKEN, HF_INFERENCE_URL, HF_MODEL

if not HF_API_TOKEN:
    print("HF_API_TOKEN is missing. Add it to repo-ai/.env", file=sys.stderr)
    sys.exit(1)

headers = {
    "Authorization": f"Bearer {HF_API_TOKEN}",
    "Content-Type": "application/json",
}

payload = {
    "model": HF_MODEL,
    "messages": [{"role": "user", "content": "Explain AI in one sentence."}],
    "max_tokens": 64,
}

print(f"URL:   {HF_INFERENCE_URL}")
print(f"Model: {HF_MODEL}")

response = requests.post(
    HF_INFERENCE_URL,
    headers=headers,
    json=payload,
    timeout=120,
)

print(f"Status: {response.status_code}")

if not response.ok:
    print(response.text[:500])
    sys.exit(1)

try:
    data = response.json()
except JSONDecodeError:
    print("Non-JSON response (often means deprecated endpoint or HTML error page):")
    print(response.text[:500])
    sys.exit(1)

print(json.dumps(data, indent=2))

# Print assistant text if present
choices = data.get("choices") or []
if choices:
    print("\n--- Assistant ---")
    print(choices[0].get("message", {}).get("content", ""))

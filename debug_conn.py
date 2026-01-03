import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

BASE = os.getenv('OPENAI_API_BASE', '').strip().strip('"').strip("'")
KEY = os.getenv('OPENAI_API_KEY', '').strip().strip('"').strip("'")
DEP = os.getenv('AZURE_DEPLOYMENT_NAME', '')
VER = os.getenv('OPENAI_API_VERSION', '2024-02-15-preview')

print(f"Testing connectivity to: {BASE}")
print(f"Deployment: {DEP}")

# Construct a test URL.
# Azure OpenAI endpoints are usually: https://{resource}.openai.azure.com/openai/deployments/{deployment}/chat/completions?api-version={version}
url = f"{BASE}/openai/deployments/{DEP}/chat/completions?api-version={VER}"

headers = {
    "api-key": KEY,
    "Content-Type": "application/json"
}

payload = {
    "messages": [
        {"role": "user", "content": "Hello"}
    ],
    "max_tokens": 5
}

try:
    print(f"Request URL: {url}")
    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    print(f"Status Code: {resp.status_code}")
    print(f"Response: {resp.text[:200]}")
except Exception as e:
    print(f"Exception: {str(e)[:200]}")

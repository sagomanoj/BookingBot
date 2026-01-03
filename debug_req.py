import requests
import sys

try:
    resp = requests.post("http://127.0.0.1:5000/api/chat", json={"message": "hello"})
    print(f"Status: {resp.status_code}")
    print(f"Content: {resp.text}")
except Exception as e:
    print(f"Caught exception: {e}")

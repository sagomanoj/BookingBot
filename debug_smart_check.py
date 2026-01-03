import requests
import sys

# Test: Check availability using DEVICE CODE directly (avoiding ID lookup step)
msg = "Check available slots for B737-8-MIA-#1 for tomorrow"
print(f"User Message: {msg}")

try:
    resp = requests.post("http://127.0.0.1:5000/api/chat", json={"message": msg})
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.json()}")
except Exception as e:
    print(f"Caught exception: {e}")
